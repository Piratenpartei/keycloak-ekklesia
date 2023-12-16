from common import create_keycloak_admin_client

RENAMES = {"ekklesia_sync_id": "sync_id"}

keycloak_admin = create_keycloak_admin_client()

keycloak_users = keycloak_admin.get_users()

#old_vals = []

user_count = len(keycloak_users)
valid_count = 0
email_count = 0
eligible_count = 0
verified_count = 0
disable_count = {}

for user in keycloak_users:
     current_attrs = user.get('attributes', {})
     if user.get("emailVerified"):
       email_count += 1
     else:
       continue
     if "ekklesia_eligible" in current_attrs:
         valid_count += 1
         if current_attrs["ekklesia_eligible"][0] == 'true':
             eligible_count += 1
         if current_attrs["ekklesia_verified"][0] == 'true':
             verified_count += 1
     elif "ekklesia_disable_reason" in current_attrs:
         key = current_attrs["ekklesia_disable_reason"][0]
         if "another" in key:
             print("Double user: " + user.get("username"))
         if key not in disable_count:
             disable_count[key] = 0
         disable_count[key] += 1
#    current_attrs = user.get('attributes', {})
#    old_vals.append(current_attrs)
#    did = False
#    if "sync_id" in current_attrs:
#        current_attrs["old_sync_id"] = current_attrs["sync_id"]
#        del current_attrs["sync_id"]
#        keycloak_admin.update_user(user_id=user["id"], payload={"attributes": current_attrs})

#print(old_vals)
print(f"Valid: {valid_count}/{email_count}/{user_count}")
print(f"Eligible: {eligible_count}; Verified: {verified_count}")
print("Disable reasons:")
for k, v in disable_count.items():
    print(f"{k}: {v}")
