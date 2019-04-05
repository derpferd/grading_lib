import json
import os
from typing import Dict, List


class Student:
    def __init__(self, x500, fname, lname):
        self.x500 = x500
        self.fname = fname
        self.lname = lname
        self.score = 0
        self.comment = ''
        self.done = False

    def get_name(self, sep=' ', reverse=False):
        name = [self.fname, self.lname]
        if reverse:
            name.reverse()
        return sep.join(name)

    def add_comment(self, s):
        if s.strip():
            self.comment += s.rstrip() + "  "

    def add_cmt(self, s):
        self.add_comment(s)

    @property
    def obj(self):
        return {'x500': self.x500,
                'fname': self.fname,
                'lname': self.lname,
                'score': self.score,
                'comment': self.comment,
                'done': self.done}

    @classmethod
    def from_obj(cls, obj):
        s = Student(obj['x500'], obj['fname'], obj['lname'])
        s.score = obj['score']
        s.comment = obj['comment']
        s.done = obj['done']
        return s

    def __repr__(self):
        return "<Student {}>".format(self.x500)

    def __str__(self):
        return self.get_name()


class StudentGroup:
    def __init__(self, submitter: str, members: List[str]):
        self.submitter = submitter
        self.members = members

    @property
    def obj(self):
        return {'submitter': self.submitter,
                'members': self.members}

    @classmethod
    def from_obj(cls, obj) -> 'StudentGroup':
        return StudentGroup(obj['submitter'], obj['members'])


class StudentDB:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

        try:
            os.mkdir(root_dir)
        except FileExistsError:
            pass  # This is ok, we just want to make sure the file exists.

    @property
    def students(self) -> Dict[str, Student]:
        students = {}
        for file in os.listdir(self.root_dir):
            with open(os.path.join(self.root_dir, file), 'r') as fp:
                obj = json.load(fp)
                student = Student.from_obj(obj)
                students[student.x500] = student
        return students

    @property
    def not_done_students(self) -> Dict[str, Student]:
        return {s.x500: s for s in self.students.values() if not s.done}

    @property
    def done_students(self) -> Dict[str, Student]:
        return {s.x500: s for s in self.students.values() if s.done}

    def get(self, x500: str):
        with open(os.path.join(self.root_dir, x500), 'r') as fp:
            obj = json.load(fp)
            return Student.from_obj(obj)

    def save(self, student: Student):
        with open(os.path.join(self.root_dir, student.x500), 'w') as fp:
            json.dump(student.obj, fp)
