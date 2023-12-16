import csv
import settings
import sys
from typing import List

from common import create_keycloak_admin_client

keycloak_admin = create_keycloak_admin_client()
keycloak_users = keycloak_admin.get_users()

def get_user(token: str):
  for user in keycloak_users:
    current_attrs = user.get('attributes', {})
    if "ekklesia_sync_id" in current_attrs:
      if current_attrs["ekklesia_sync_id"][0] == token:
        return user
  return None


def read_file(file_name: str) -> List[dict]:
  with open(file_name, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, quotechar=settings.csv_quotechar, strict=True, delimiter=settings.csv_delimiter)
    user_rows = list(reader)
  return user_rows

content_new = read_file(sys.argv[2])
content_old = read_file(sys.argv[1])


def print_info(data):
  user_count = len(data)
  eligible_count = 0
  verified_count = 0
  for user in data:
    if user[settings.field_eligible] == "-1":
      eligible_count += 1
    if user[settings.field_verified] and user[settings.field_verified] != 'NULL':
      verified_count += 1
  print(f"Users: {user_count}")
  print(f"Eligible: {eligible_count}; Verified: {verified_count}")

print("==NEW==")
print_info(content_new)
print("==OLD==")
print_info(content_old)

print("==NEW USERS")

list_of_old = []
for elem in content_old:
  list_of_old.append(elem[settings.field_sync_id])

for elem in content_new:
  field = elem[settings.field_sync_id]
  if field not in list_of_old:
    user = get_user(field)
    if user:
      print("REGISTERED Name: ", user.get("username"), elem)
    else:
      print(elem)
