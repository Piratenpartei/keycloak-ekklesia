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
from typing import List, Optional, Set
import keycloak

import typer
from eliot import start_action, start_task, to_file, register_exception_extractor, log_message
from eliot.stdlib import EliotHandler

import settings
from common import create_keycloak_admin_client

URL_ADMIN_USER_LOGOUT = "admin/realms/{realm-name}/users/{id}/logout"

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(EliotHandler())
to_file(sys.stdout)
logging.captureWarnings(True)


# XXX: use Pydantic for validation
@dataclass
class UserUpdate:
    email: str
    sync_id: str
    verified: Optional[bool] = None
    eligible: Optional[bool] = None
    department: Optional[str] = None


def prepare_user_updates(csv_filepath: str) -> List[UserUpdate]:

    with start_action(action_type="read_user_csv", csv_filepath=csv_filepath) as action:
        with open(csv_filepath) as f:
            reader = csv.DictReader(f, quotechar=settings.csv_quotechar, strict=True, delimiter=settings.csv_delimiter)
            user_rows = list(reader)

        action.add_success_fields(len_user_rows=len(user_rows))

    users = []

    with start_action(action_type="prepare_updates"):
        for ll, row in enumerate(user_rows):
            try:
                sync_id = row[settings.field_sync_id]
                user = UserUpdate(
                    email=row[settings.field_email],
                    sync_id=sync_id
                )
                if settings.field_verified:
                    user.verified = row[settings.field_verified] == "1"
                if settings.field_eligible:
                    user.eligible = row[settings.field_eligible] == "1"
                if settings.field_department:
                    user.department = row[settings.field_department]
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


def get_user_update(user, updates_by_email, updates_by_sync_id, used_sync_ids: Set[str], duplicate_sync_ids: Set[str]):

    with start_action(action_type="get_user_update") as action:
        keycloak_sync_id = get_attr(user.get('attributes'), "sync_id")
        keycloak_sync_id = keycloak_sync_id.strip() if keycloak_sync_id else ""
        keycloak_email = user['email']

        if keycloak_sync_id:
            # 1. user has mail and sync_id attr => new user with manually entered token or existing user
            user_update_by_sync_id = updates_by_sync_id.get(keycloak_sync_id)
            user_update_by_mail = updates_by_email.get(keycloak_email)

            if user_update_by_sync_id is None:
                raise SyncCheckFailed("1.1", "unknown sync id")

            if not get_attr(user.get('attributes'), "first_sync"):
                # New user!
                if keycloak_sync_id in duplicate_sync_ids:
                    raise SyncCheckFailed("1.2", "new user, sync id also used by another user!")

            if user_update_by_mail is None:
                action.add_success_fields(
                    case="1.3",
                    text=
                    "sync id does not match member's mail address, ok because address doesn't belong to another member"
                )
            elif user_update_by_mail == user_update_by_sync_id:
                action.add_success_fields(case="1.4", text="sync id matches email")
            else:
                raise SyncCheckFailed(
                    "1.5", "sync id does not match member's mail address, other member with that address found"
                )

        else:
            # 2. user has mail but no sync_id attr => new user
            user_update_by_mail = updates_by_email.get(keycloak_email)
            user_update_by_sync_id = None

            if user_update_by_mail:
                if user_update_by_mail.sync_id in used_sync_ids:
                    raise SyncCheckFailed("2.3", "new user, mail match would create second user for an existing sync id!")

                action.add_success_fields(case="2.1", text="new user, no sync id, known email")
            else:
                raise SyncCheckFailed("2.2", "new user, no sync id, unknown mail")

    return user_update_by_mail or user_update_by_sync_id


def get_attr(attributes, attrname, default=None):
    """XXX: use Pydantic for validation and conversion
    """
    if not attributes:
        return default

    value = attributes.get(attrname, [default])[0]
    if value == "true":
        return True
    elif value == "false":
        return False
    else:
        return value


def update_keycloak_user_attrs(keycloak_admin, user, user_update):

    with start_action(action_type="update_keycloak_user_attrs") as action:
        current_attrs = user.get('attributes', {})

        now_iso = datetime.now(timezone.utc).isoformat()

        updated_attrs = {
            **current_attrs,
            'verified': user_update.verified,
            'eligible': user_update.eligible,
            "sync_id": user_update.sync_id,
            "last_sync": now_iso
        }

        if "first_sync" not in current_attrs:
            updated_attrs["first_sync"] = now_iso
            action.add_success_fields(is_first_sync=True)
        else:
            action.add_success_fields(previous_sync=get_attr(current_attrs, "last_sync"))
            changed = {}

            if get_attr(current_attrs, "verified") != user_update.verified:
                changed["verified"] = [get_attr(current_attrs, "verified"), user_update.verified]

            if get_attr(current_attrs, "eligible") != user_update.eligible:
                changed["eligible"] = [get_attr(current_attrs, "eligible"), user_update.eligible]

            if changed:
                action.add_success_fields(changed=changed)

        if "disable_reason" in current_attrs:
            del updated_attrs["disable_reason"]

        keycloak_admin.update_user(user_id=user["id"], payload={"attributes": updated_attrs, "enabled": True})


def update_keycloak_user_group(keycloak_admin, default_group_id, user, user_update, group_ids_by_name):
    with start_action(action_type="update_keycloak_user_group") as action:
        user_id = user["id"]

        wanted_group_id = group_ids_by_name.get(user_update.department)
        if wanted_group_id is None:
            wanted_group_id = default_group_id
            action.log(
                message_type="unknown_group",
                group=user_update.department,
                msg="no known department name given, using default group")

        if settings.generate_missing_display_names:
            group = keycloak_admin.get_group(wanted_group_id)
            if not group or not get_attr(group["attributes"], "display_name"):
                with open(settings.missing_display_name_file, "r+") as file:
                    if group["name"] not in file.read():
                        print(group["name"], file=file)

        group_found = False
        for group in keycloak_admin.get_user_groups(user_id):
            if group["id"] == wanted_group_id:
                group_found = True
            elif group["path"].startswith(settings.parent_group_path):
                with start_action(action_type="group_user_remove", group_id=group["id"], group_name=group["name"]):
                    keycloak_admin.group_user_remove(user_id, group["id"])

        if not group_found:
            with start_action(action_type="group_user_add", group_id=wanted_group_id, group_name=user_update.department):
                keycloak_admin.group_user_add(user_id, wanted_group_id)


def remove_user_attributes_and_groups(keycloak_admin, user, do_update=True):
    with start_action(action_type="remove_user_attributes"):
        current_attrs = user.get('attributes', {})

        updated_attrs = {
            **current_attrs
        }

        # Delete verified and eligible state
        if "verified" in updated_attrs:
            del updated_attrs["verified"]

        if "eligible" in updated_attrs:
            del updated_attrs["eligible"]

        # Delete all groups
        for group in keycloak_admin.get_user_groups(user["id"]):
            if group["path"].startswith(settings.parent_group_path):
                with start_action(action_type="group_user_remove", group_id=group["id"], group_name=group["name"]):
                    keycloak_admin.group_user_remove(user["id"], group["id"])

        if do_update:
            keycloak_admin.update_user(user_id=user["id"], payload={"attributes": updated_attrs})

        return updated_attrs


def disable_keycloak_user(keycloak_admin, user, reason):
    with start_action(action_type="disable_keycloak_user"):

        attributes = remove_user_attributes_and_groups(keycloak_admin, user, False)
        attributes["disable_reason"] = reason

        keycloak_admin.update_user(user_id=user["id"], payload={"attributes": attributes, "enabled": False})


def logout_everywhere(keycloak_admin, user):
    with start_action(action_type="logout_everywhere"):
        params = {"realm-name": keycloak_admin.realm_name, "id": user["id"]}
        data_raw = keycloak_admin.raw_post(URL_ADMIN_USER_LOGOUT.format(**params), data=None)
        keycloak.raise_error_from_response(data_raw, keycloak.KeycloakGetError, expected_codes=[204])


def get_used_and_dup_sync_ids(keycloak_users: List[dict]):
    with start_action(action_type="get_used_and_dup_sync_ids") as action:
        users_by_sync_id = {}
        for user in keycloak_users:
            sync_id = get_attr(user.get('attributes'), 'sync_id')
            sync_id = sync_id.strip() if sync_id else ""

            if sync_id:
                users_with_same_sync_id = users_by_sync_id.setdefault(sync_id, [])
                users_with_same_sync_id.append(user)

        duplicate_sync_ids = set()

        for sync_id, users in users_by_sync_id.items():
            if len(users) > 1:
                duplicate_sync_ids.add(sync_id)
                action.log(
                    message_type="duplicate_sync_id",
                    sync_id=sync_id,
                    user_ids=[u["id"] for u in users],
                    text="warning, same sync id used for more than one user in keycloak!")

        return set(users_by_sync_id), duplicate_sync_ids


def update_keycloak_users(user_updates: List[UserUpdate]):

    keycloak_admin = create_keycloak_admin_client()

    with start_action(action_type="get_keycloak_users") as action:
        keycloak_users = keycloak_admin.get_users({'search': '@'})
        action.add_success_fields(keycloak_users=len(keycloak_users))

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

    used_sync_ids, duplicate_sync_ids = get_used_and_dup_sync_ids(keycloak_users)

    keycloak_users_no_verified_email = [user for user in keycloak_users if not user.get("emailVerified")]

    with start_action(action_type="non_verified_users"):
        for user in keycloak_users_no_verified_email:
            remove_user_attributes_and_groups(keycloak_admin, user)
            logout_everywhere(keycloak_admin, user)

    keycloak_users_verified_email = [user for user in keycloak_users if user.get("emailVerified")]

    with start_action(action_type="update_keycloak"):
        for user in keycloak_users_verified_email:
            try:
                with start_action(action_type="update_keycloak_user", user_id=user["id"]):
                    user_update = get_user_update(user, updates_by_email, updates_by_sync_id, used_sync_ids, duplicate_sync_ids)
                    update_keycloak_user_attrs(keycloak_admin, user, user_update)
                    update_keycloak_user_group(keycloak_admin, parent_group["id"], user, user_update, group_ids_by_name)

            # Disable if syncing failed for a user (e.g. user no longer a member)
            except SyncCheckFailed as e:
                with start_action(action_type="sync_check_failed", user_id=user["id"], problem=str(e)):
                    disable_keycloak_user(keycloak_admin, user, str(e))
                    logout_everywhere(keycloak_admin, user)

            # Ignore other exceptions
            except Exception:
                log_message(message_type="user_update_exception", user_id=user["id"], exception=e)


def main(csv_filepath: str):
    with start_task(action_type="update_users"):
        # Clear missing display names file
        open(settings.missing_display_name_file, 'w').close()

        user_updates = prepare_user_updates(csv_filepath)
        update_keycloak_users(user_updates)


if __name__ == "__main__":
    typer.run(main)
