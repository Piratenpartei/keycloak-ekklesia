import typer
from eliot import start_action, start_task, log_message

import urllib.request
import json

import matrix_settings
from common import create_keycloak_admin_client

allowed_roles = ["Mitarbeiter", "Piratenpartei Deutschland"]

def get_allowed_keycloak_users():
    keycloak_admin = create_keycloak_admin_client()

    with start_action(action_type="get_keycloak_users") as action:
        keycloak_users = keycloak_admin.get_users()
        action.add_success_fields(keycloak_users=len(keycloak_users))

    allowed_ids = []
    with start_action(action_type="get_allowed_users") as action:
        for user in keycloak_users:
            roles = user.get('realmRoles')
            if roles:
                for role in roles:
                    if role in allowed_roles:
                        allowed_ids.append(user.get('id'))
                        break

        action.add_success_fields(allowed_users=len(allowed_ids))

    return allowed_ids

def get_matrix_user(user):
    with start_action(action_type="get_matrix_user", user=user["name"]) as action:
        headers = {"Authorization", "Bearer " + matrix_settings.matrix_token}
        try:
            req = urllib.request.Request("http://localhost:8008/_synapse/admin/v2/users" + user['name'], headers=headers)
            answer = json.loads(urllib.request.urlopen(req).read())
        except Exception as e:
            log_message(message_type="user_retrieve_exception", user_id=user["name"], exception=e)
            return None

        oidc_id = None
        if "external_ids" in answer:
            for provider in answer["external_ids"]:
                if provider["auth_provider"] == "oidc-keycloak":
                    oidc_id = provider["external_id"]
        if oidc_id:
            return (user["name"], oidc_id)
        else:
            return None

def get_all_matrix_users():
    with start_action(action_type="get_matrix_users") as action:
        next = 0
        users = []
        while next:
            headers = {"Authorization", "Bearer " + matrix_settings.matrix_token}
            req = urllib.request.Request("http://localhost:8008/_synapse/admin/v2/users?from=" + next, headers=headers)
            answer = json.loads(urllib.request.urlopen(req).read())
            next = answer['next_token'] if 'next_token' in answer else None
            answer_users = answer['users'] if 'users' in answer else []
            for user in answer_users:
                matrix_user = get_matrix_user(user)
                if matrix_user:
                    users.append(matrix_user)

        action.add_success_fields(matrix_users=len(users))

        return users

def log_out_of_matrix(user_name):
    headers = {"Authorization", "Bearer " + matrix_settings.matrix_token}
    data = '{"erase": false}'
    req = urllib.request.Request("http://localhost:8008/_synapse/admin/v1/deactivate/" + user_name, headers=headers, data=data, method='POST')

    try:
        urllib.request.urlopen(req)
    except:
        pass

def main():
    with start_task(action_type="clear_matrix"):
        keycloak_users = get_allowed_keycloak_users()
        matrix_users = get_all_matrix_users()
        for (user_name, oidc_id) in matrix_users:
            if oidc_id not in keycloak_users:
                # User not allowed, force log out
                log_message(message_type="log_out_user", user_id=user_name)
                #log_out_of_matrix(user_name)

if __name__ == "__main__":
    typer.run(main)
