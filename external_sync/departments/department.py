from dataclasses import dataclass
from typing import List

from dataclasses_json import DataClassJsonMixin


@dataclass
class Department(DataClassJsonMixin):
    internal_name: str
    name: str
    children: List["Department"]
