from common import create_keycloak_admin_client
import sys

if len(sys.argv) < 2:
  print("Usage: ", sys.argv[0], "<token>")
  exit(1)

keycloak_admin = create_keycloak_admin_client()
keycloak_users = keycloak_admin.get_users()

for user in keycloak_users:
     current_attrs = user.get('attributes', {})
     if "ekklesia_sync_id" in current_attrs:
       if current_attrs["ekklesia_sync_id"][0] == sys.argv[1]:
         print("Found: ", user.get("username"))

print("End")
