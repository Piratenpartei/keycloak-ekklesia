# Sync with External Systems

## Dependencies

Dependencies are managed for all Python scripts at once.
You can run the scripts in a [poetry shell](https://python-poetry.org/docs/cli/#shell).
Use `poetry install` to install the defined dependencies.

There's also a requirements.txt that can be used to [pip-install deps in a virtualenv](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/).

## Set up Keycloak client
To be able to connect to Keycloak, a client has to be set up using the following steps:
- In the master realm create a new client (and put the name into settings.py under client_id)
- Change access type to "confidential"
- Disable "Direct access grants enabled" and "Standard flow enabled"
- Enable "Service accounts enabled"
- Save the page
- Go to the Credentials tab, copy the Secret and put it into the settings.py (variable client_secret)
- Go to the Service account roles tab, select "<realm-name>-realm" under Client Roles. (Where <realm-name> is the name of the target realm)
- Add "manage-users" to the assigned roles.
- Done! You should be able to use the scripts as described below.

## Update Users

Imports user data from CSV and updates the corresponding Keycloak user.
Users are matched by sync id primarily.
The mail address is used for matching if the sync id is missing in Keycloak.
If both are given, the mail address must match the sync id.
Mismatches and unknown sync ids are treated as errors.

If the user can be matched, user's group and optional attributes eligible and verified are set.

See test.csv and settings.example.py to understand the expected input format.

- Create a settings.py based on settings.example.py.
- Run:
  ~~~
  python update_users.py test.csv | eliot-tree
  ~~~

Logs are produced in JSON format, eliot-tree provides a nice tree view of the log entries.

## Import departments

Imports department data from CSV and creates/updates the corresponding Keycloak groups.
As an artifact, a hierarchical JSON file is generated.

To convert the CSV to JSON, type:
  ~~~
  python department.py parse departments.json departments.csv | eliot-tree
  ~~~

To import the JSON file into Keycloak, use:
  ~~~
  python department.py update departments.json | eliot-tree
  ~~~

The script will create the hierarchical department structure in Keycloak by

- Creating nonexistent departments
- Updating still existent departments (only the display name)
- Deleting no longer existing departments

The display name is saved as the attribute `display_name` of the group.
