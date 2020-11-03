import keycloak

from eliot import start_action, start_task, log_message

from common import create_keycloak_admin_client
from departments.department import Department


def load_departments_json(json_filepath: str) -> Department:
    with start_action(action_type="load_departments_json"):
        with open(json_filepath, 'r') as infile:
            content = infile.read()

        return Department.from_json(content)


def create_department_group(keycloak_admin: keycloak.KeycloakAdmin, department: Department, parent_id=None, path="/"):
    with start_action(action_type="create_department_group", department=department.internal_name, path=path):
        # Create or update group
        keycloak_admin.create_group({"name": department.internal_name, "attributes": {"display_name": [department.name]}},
                                    parent=parent_id, skip_exists=True)

        # Extend path
        path += department.internal_name

        # Get group id
        try:
            created_group = keycloak_admin.get_group_by_path(path, search_in_subgroups=True)
        except keycloak.KeycloakGetError as e:
            log_message(message_type="get_group_failed", exception=e)
            return

        # Add slash to group path
        path += "/"

        # Create groups for sub departments
        subgroup_names = []
        for sub_department in department.children:
            create_department_group(keycloak_admin, sub_department, parent_id=created_group["id"], path=path)
            subgroup_names.append(sub_department.internal_name)

        # Delete old subgroups
        for old_group in created_group["subGroups"]:
            if old_group["name"] not in subgroup_names:
                keycloak_admin.delete_group(old_group["id"])


def update(json_filepath: str):
    with start_task(action_type="update_departments"):
        departments = load_departments_json(json_filepath)

        keycloak_admin = create_keycloak_admin_client()

        create_department_group(keycloak_admin, departments)
