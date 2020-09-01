### Keycloak settings
keycloak_url = "https://keycloak.test.invalid/auth/"
client_id = "admin-api"
client_secret = "4100000d-d383-4c39-b16e-ce00000b3131f"
realm = "users"
parent_group_path = "/org"

### CSV input format.
csv_quotechar = '"'
csv_delimiter = ","
# Mandatory fields
field_email = "email"
field_sync_id = "sync_id"
# Optional fields. Set to None to ignore.
field_verified = "verified"
field_eligible = "eligible"
field_department = "department"
