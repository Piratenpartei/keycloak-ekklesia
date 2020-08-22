import csv
import hmac
import logging
import secrets
import string
import sys
from dataclasses import dataclass
from typing import List

import typer
from eliot import start_action, start_task, to_file
from eliot.stdlib import EliotHandler
from keycloak import KeycloakAdmin

import settings

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(EliotHandler())
to_file(sys.stdout)
logging.captureWarnings(True)


@dataclass
class NewUser:
    username: str
    password: str
    sync_id: str


def create_keycloak_admin_client() -> KeycloakAdmin:

    return KeycloakAdmin(
        server_url=settings.server_url,
        realm_name=settings.realm,
        client_id=settings.client_id,
        client_secret_key=settings.client_secret,
        user_realm_name="master",
        verify=True
    )


def derive_sync_id(mid: int) -> str:
    hm = hmac.new(bytes(settings.secret_sync_id_key, "ascii"), bytes(str(mid), "ascii"), 'sha3_256')
    sync_id = hm.hexdigest()
    return sync_id


def prepare_user_data(csv_filepath: str) -> List[NewUser]:

    with start_action(action_type="read_user_csv") as action:
        with open(csv_filepath) as f:
            reader = csv.DictReader(f, quotechar='"', strict=True, delimiter=';')
            user_rows = list(reader)

        action.add_success_fields(len_user_rows=len(user_rows))

    users_to_create = []

    for row in user_rows:
        with start_action(action_type="prepare_user") as action:
            username = "".join(secrets.choice(string.ascii_lowercase) for _ in range(16))
            password = username
            sync_id = derive_sync_id(row[settings.id_field_name])

            new_user = NewUser(username=username, password=password, sync_id=sync_id)

            users_to_create.append(new_user)
            action.add_success_fields(name=username, sync_id=sync_id)

    return users_to_create


def create_keycloak_users(users: List[NewUser]):

    keycloak_admin = create_keycloak_admin_client()

    for user in users:

        user_info = {
            "username": user.username,
            "enabled": True,
            "credentials": [{
                "value": user.password,
                "type": "password"
            }],
            "attributes": {
                "sync_id": user.sync_id
            },
        }

        with start_action(action_type="create_keycloak_user", sync_id=user.sync_id):
            keycloak_admin.create_user(user_info)


def main(csv_filepath: str):
    with start_task(action_type="create_users", csv_filepath=csv_filepath):
        users_to_create = prepare_user_data(csv_filepath)
        create_keycloak_users(users_to_create)


if __name__ == "__main__":
    typer.run(main)
