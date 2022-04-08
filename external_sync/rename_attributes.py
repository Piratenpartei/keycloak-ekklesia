from common import create_keycloak_admin_client

# RENAMES = {"first_sync": "ekklesia_first_sync", "last_sync": "ekklesia_last_sync", "verified": "ekklesia_verified",
#           "eligible": "ekklesia_eligible", "department": "ekklesia_department", "sync_id": "ekklesia_sync_id",
#           "disable_reason": "ekklesia_disable_reason", "disable_time": "ekklesia_disable_time", "old_attrs": "ekklesia_old_attrs"}
RENAMES = {"ekklesia_sync_id": "sync_id"}

keycloak_admin = create_keycloak_admin_client()

keycloak_users = keycloak_admin.get_users()

old_vals = []

for user in keycloak_users:
    current_attrs = user.get('attributes', {})
    old_vals.append(current_attrs)
    did = False
    for key, val in RENAMES.items():
        if key in current_attrs:
            current_attrs[val] = current_attrs[key]
            del current_attrs[key]
            did = True
        pass

    if did:
        keycloak_admin.update_user(user_id=user["id"], payload={"attributes": current_attrs})

print(old_vals)

