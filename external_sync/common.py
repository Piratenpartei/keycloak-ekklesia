from eliot import start_action
from keycloak import KeycloakAdmin

import settings


def create_keycloak_admin_client() -> KeycloakAdmin:

    with start_action(action_type="create_keycloak_admin_client"):
        return KeycloakAdmin(
            server_url=settings.keycloak_url,
            realm_name=settings.realm,
            user_realm_name="master",
            client_id=settings.client_id,
            client_secret_key=settings.client_secret,
            verify=True,
            auto_refresh_token=['get', 'post', 'put', 'delete']
        )
