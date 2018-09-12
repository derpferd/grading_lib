import json
import os
from typing import Dict, Optional

from grading_lib.db.student import StudentGroup


class GroupsDB:
    def __init__(self, root_dir: str='data/groups'):
        self.root_dir = root_dir

        if not os.path.exists(root_dir):
            os.mkdir(root_dir)

    @property
    def groups(self) -> Dict[str, StudentGroup]:  # submitter: group
        groups = {}
        for file in os.listdir(self.root_dir):
            with open(os.path.join(self.root_dir, file), 'r') as fp:
                obj = json.load(fp)
                group = StudentGroup.from_obj(obj)
                groups[group.submitter] = group
        return groups

    def get(self, x500) -> Optional[StudentGroup]:
        for group in self.groups.values():
            if x500 in group.members:
                return group
        return None

    def save(self, group: StudentGroup):
        with open(os.path.join(self.root_dir, group.submitter), 'w') as fp:
            json.dump(group.obj, fp)
