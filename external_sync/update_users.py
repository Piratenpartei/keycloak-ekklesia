"""
We assume that users register themselves with a known member mail address and/or a valid sync_id ("register token").
If both sync_id and mail are given, we accept all mail addresses that are not associated with another member.

Expected CSV format and Keycloak access settings can be configured via settings.py

"""
import csv
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List
from keycloak import keycloak_admin

import typer
from eliot import start_action, start_task, to_file, register_exception_extractor, log_message
from eliot.stdlib import EliotHandler
from keycloak import KeycloakAdmin

import settings

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(EliotHandler())
to_file(sys.stdout)
logging.captureWarnings(True)


def create_keycloak_admin_client() -> KeycloakAdmin:

    with start_action(action_type="create_keycloak_admin_client"):
        return KeycloakAdmin(
            server_url=settings.keycloak_url,
            realm_name=settings.realm,
            client_id=settings.client_id,
            client_secret_key=settings.client_secret,
            user_realm_name="master",
            verify=True
        )

# XXX: use Pydantic for validation
@dataclass
class UserUpdate:
    email: str
    sync_id: str
    verified: bool
    eligible: bool
    department: str


def prepare_user_updates(csv_filepath: str) -> List[UserUpdate]:

    with start_action(action_type="read_user_csv", csv_filepath=csv_filepath) as action:
        with open(csv_filepath) as f:
            reader = csv.DictReader(f, quotechar=settings.csv_quotechar, strict=True, delimiter=settings.csv_delimiter)
            user_rows = list(reader)

        action.add_success_fields(len_user_rows=len(user_rows))

    users = []

    with start_action(action_type="prepare_updates") as action:
        for ll, row in enumerate(user_rows):
            try:
                sync_id = row[settings.field_sync_id]

                user = UserUpdate(
                    email=row[settings.field_email],
                    sync_id=sync_id,
                    verified=row[settings.field_verified] == "1",
                    eligible=row[settings.field_eligible] == "1",
                    department=row[settings.field_department]
                )
                users.append(user)
            except Exception as e:
                log_message(message_type="prepare_user_failure", line=ll, exception=e)

    return users


def find_all_groups(group):
    if group['subGroups']:
        return [g for group in group['subGroups'] for g in find_all_groups(group)] + [group]
    else:
        return [group]


class SyncCheckFailed(Exception):

    def __init__(self, case, text):
        self.case = case
        super().__init__(text)


register_exception_extractor(SyncCheckFailed, lambda e: {"case": e.case})


def get_user_update(user, updates_by_email, updates_by_sync_id):

    with start_action(action_type="get_user_update") as action:
        keycloak_sync_id = user['attributes'].get('sync_id', [''])[0]
        keycloak_email = user['email']

        if keycloak_sync_id:
            # 1. user has mail and sync_id attr => new user with manually entered token or existing user
            user_update_by_sync_id = updates_by_sync_id.get(keycloak_sync_id)
            user_update_by_mail = updates_by_email.get(keycloak_email)

            if user_update_by_sync_id is None:
                raise SyncCheckFailed("1.1", "unknown sync id")
            elif user_update_by_mail is None:
                action.add_success_fields(
                    case="1.2",
                    text=
                    "sync id does not match member's mail address, ok because address doesn't belong to another member"
                )
            elif user_update_by_mail == user_update_by_sync_id:
                action.add_success_fields(case="1.3", text="sync id matches email")
            else:
                raise SyncCheckFailed(
                    "1.4", "sync id does not match member's mail address, other member with that address found"
                )

        else:
            # 2. user has mail but no sync_id attr => new user
            user_update_by_mail = updates_by_email.get(keycloak_email)
            user_update_by_sync_id = None
            if user_update_by_mail:
                action.add_success_fields(case="2.1", text="no sync id, known email")
            else:
                raise SyncCheckFailed("2.2", "no sync id, unknown mail")

    return user_update_by_mail or user_update_by_sync_id


def update_keycloak_user_attrs(keycloak_admin, user, user_update):

    with start_action(action_type="update_keycloak_user_attrs") as action:
        current_attrs = user['attributes']

        def get_user_attr(attrname, default=None):
            """XXX: use Pydantic for validation and conversion
            """
            value = current_attrs.get(attrname, [default])[0]
            if value == "true":
                return True
            elif value == "false":
                return False
            else:
                return value

        now_iso = datetime.now(timezone.utc).isoformat()

        updated_attrs = {
            **current_attrs, 'verified': user_update.verified,
            'eligible': user_update.eligible,
            "sync_id": user_update.sync_id,
            "last_sync": now_iso
        }

        if "last_sync" not in user["attributes"]:
            updated_attrs["first_sync"] = now_iso
            action.add_success_fields(is_first_sync=True)
        else:
            action.add_success_fields(previous_sync=get_user_attr("last_sync"))
            changed = {}

            if get_user_attr("verified") != user_update.verified:
                changed["verified"] = [get_user_attr("verified"), user_update.verified]

            if get_user_attr("eligible") != user_update.eligible:
                changed["eligible"] = [get_user_attr("eligible"), user_update.eligible]

            if changed:
                action.add_success_fields(changed=changed)

        keycloak_admin.update_user(user_id=user["id"], payload={"attributes": updated_attrs})


def update_keycloak_user_group(keycloak_admin, user, user_update, group_ids_by_name):
    with start_action(action_type="update_keycloak_user_group"):
        user_id = user["id"]

        wanted_group_id = group_ids_by_name[user_update.department]
        group_found = False
        for group in keycloak_admin.get_user_groups(user_id):
            if group["id"] == wanted_group_id:
                group_found = True
            else:
                with start_action(action_type="group_user_remove", group_id=group["id"], group_name=group["name"]):
                    keycloak_admin.group_user_remove(user_id, group["id"])

        if not group_found:
            with start_action(action_type="group_user_add", group_id=wanted_group_id, group_name=user_update.department):
                keycloak_admin.group_user_add(user_id, wanted_group_id)


def update_keycloak_users(user_updates: List[UserUpdate]):

    keycloak_admin = create_keycloak_admin_client()

    with start_action(action_type="get_keycloak_users") as action:
        keycloak_users = keycloak_admin.get_users({'search': '@'})
        action.add_success_fields(num_keycloak_users=len(keycloak_users))

    with start_action(action_type="get_keycloak_groups") as action:
        parent_group = keycloak_admin.get_group_by_path(settings.parent_group_path)
        group_ids_by_name = {g['name']: g['id'] for g in find_all_groups(parent_group)}
        action.add_success_fields(
            parent_group_name=parent_group["name"],
            parent_group_id=parent_group["id"],
            num_groups=len(group_ids_by_name)
        )

    updates_by_sync_id = {u.sync_id: u for u in user_updates}
    updates_by_email = {u.email: u for u in user_updates}

    with start_action(action_type="update_keycloak"):
        for user in keycloak_users:
            try:
                with start_action(action_type="update_keycloak_user", user_id=user["id"]):
                    user_update = get_user_update(user, updates_by_email, updates_by_sync_id)
                    update_keycloak_user_attrs(keycloak_admin, user, user_update)
                    update_keycloak_user_group(keycloak_admin, user, user_update, group_ids_by_name)

            # Just go on if syncing failed for a user
            except Exception:
                pass


def main(csv_filepath: str):
    with start_task(action_type="update_users"):
        user_updates = prepare_user_updates(csv_filepath)
        update_keycloak_users(user_updates)


if __name__ == "__main__":
    typer.run(main)
