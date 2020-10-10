import csv
from datetime import datetime
from typing import List, Optional

from eliot import start_action, start_task, log_message

from departments import settings
from departments.department import Department


def get_department_name(row, name_field_num) -> Optional[str]:
    name = None

    if type(settings.name_fields[name_field_num]) is list:
        for name_field in settings.name_fields[name_field_num]:
            if row[name_field]:
                name = row[name_field]
                break
    else:
        name_field = settings.name_fields[name_field_num]
        if row[name_field]:
            name = row[name_field]

    return name


def parse_department(department, departments, cur_i, name_field_num=0) -> (int, List[Department]):
    """
    Computes all sub-departments for the given department.

    :param department: The current department (may be a dummy department when a certain layer doesn't exist)
    :param departments: The list of all departments
    :param cur_i: The next department id in the department list
    :param name_field_num: The current id of the name field to use
    :return: Returns the current department id
    """
    name_field_num += 1

    unassigned_departments = []

    while cur_i < len(departments):
        row = departments[cur_i]
        internal_name = row[settings.internal_name]

        with start_action(action_type="parse_department", row=cur_i, name_field=settings.name_fields[name_field_num], internal_name=internal_name) as action:

            try:
                higher_level = False
                for i in range(name_field_num):
                    # Department on higher level
                    if get_department_name(row, i):
                        higher_level = True
                        break

                if higher_level:
                    action.add_success_fields(state="higher_level")
                    break

                # Department doesn't exist anymore
                ignore_after_date = row[settings.ignore_after_name]
                if ignore_after_date and datetime.strptime(ignore_after_date, settings.ignore_after_format) <= datetime.now():
                    cur_i += 1
                    action.add_success_fields(state="disbanded")
                    continue

                name = get_department_name(row, name_field_num)

                child_department = Department(
                    internal_name=internal_name,
                    name=name,
                    children=[]
                )

                # Valid department on this level, sub departments start on next line
                if name:
                    action.add_success_fields(name=name)
                    next_line = cur_i+1
                # Invalid department on this level, this may be a sub department
                else:
                    action.add_success_fields(name="Empty")
                    next_line = cur_i

                # Parse children if not already at lowest department level
                if len(settings.name_fields) > name_field_num + 1:
                    (cur_i, unassigned_sub_departments) = parse_department(child_department, departments, next_line, name_field_num)
                    unassigned_departments += unassigned_sub_departments
                    action.add_success_fields(unassigned_sub_departments=len(unassigned_sub_departments))

                # Valid department on this level
                if name:
                    action.add_success_fields(state="valid")
                    department.children.append(child_department)

                # No valid department, but valid on lower level
                elif len(child_department.children) > 0:
                    action.add_success_fields(state="valid_lower_level")
                    department.children += child_department.children

                # No valid department on any level (no name given)
                else:
                    action.add_success_fields(state="unassigned")
                    # Add as child to default layer department (we just don't know if the level is right)
                    unassigned_departments.append(child_department)

                # Add all unassigned departments (having no valid name) from lower levels if this is the default level
                if len(unassigned_departments) > 0 and name_field_num == settings.name_default and name:
                    child_department.children += unassigned_departments
                    action.add_success_fields(unassigned_taken=len(unassigned_departments))
                    unassigned_departments.clear()

                action.add_success_fields(children=len(child_department.children))

            except Exception as e:
                log_message(message_type="parse_department_failure", line=cur_i, exception=e)

            cur_i += 1

    return cur_i - 1, unassigned_departments


def parse_departments(csv_filepath: str) -> Department:

    with start_action(action_type="read_department_csv", csv_filepath=csv_filepath) as action:
        with open(csv_filepath) as f:
            reader = csv.DictReader(f, quotechar=settings.csv_quotechar, strict=True, delimiter=settings.csv_delimiter)
            departments = list(reader)

        action.add_success_fields(len_department_rows=len(departments))

    main_department = Department(
        internal_name=departments[0][settings.internal_name],
        name=get_department_name(departments[0], 0),
        children=[]
    )

    action.add_success_fields(main_department=main_department.name)

    parse_department(main_department, departments, 1)

    return main_department


def write_departments_json(departments: Department, json_filepath: str):
    with start_action(action_type="write_departments_json"):
        content = departments.to_json()
        with open(json_filepath, 'w') as outfile:
            outfile.write(content)


def parse(json_filepath: str, csv_filepath: str):
    with start_task(action_type="parse_departments"):
        departments = parse_departments(csv_filepath)
        write_departments_json(departments, json_filepath)
