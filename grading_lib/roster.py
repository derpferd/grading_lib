from __future__ import print_function
import io
import csv
import json
from enum import Enum
from typing import List, Dict, TextIO


class Student(object):
    def __init__(self, x500, fname, lname, external_id=None, extra_tags: Dict[str, str]=None):
        self.x500 = x500
        self.fname = fname
        self.lname = lname
        self.external_id = external_id
        self.extra_tags = extra_tags
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
                'external_id': self.external_id,
                'extra_tags': self.extra_tags,
                'score': self.score,
                'comment': self.comment,
                'done': self.done}

    @classmethod
    def from_obj(cls, obj):
        s = Student(obj['x500'], obj['fname'], obj['lname'], obj.get('external_id', None), obj.get('extra_tags', None))
        s.score = obj['score']
        s.comment = obj['comment']
        s.done = obj['done']
        return s

    def __repr__(self):
        return "<Student {}>".format(self.x500)

    def __str__(self):
        return self.get_name()


class StudentGroup(list):
    def __init__(self, students: List[Student]):
        super().__init__(students)


class OutputFormat(Enum):
    MOODLE = 0
    CANVAS = 1


class Roster(object):
    students: Dict[str, Student]  # sid -> student
    groups: List[StudentGroup]
    group_submitters: Dict[Student, StudentGroup]

    def __init__(self, roster_path='../roster.csv'):
        self.students = {}
        self.groups = []
        self.group_submitters = {}

        # read in students
        with open(roster_path, 'r', newline='') as fp:
            roster_reader = csv.DictReader(fp)
            for row in roster_reader:
                sid = row['x500'].strip()
                fname = row['first name'].strip()
                lname = row['last name'].strip()
                external_id = row['ID'].strip()
                if isinstance(external_id, str):
                    external_id = external_id.strip()
                extra_tags = {}
                for key, value in row.items():
                    if key not in {'x500', 'first name', 'last name', 'id'}:
                        extra_tags[key] = value.strip()
                self.students[sid] = Student(sid, fname, lname, external_id, extra_tags)

    def __iter__(self):
        return iter(sorted(self.students.values(), key=lambda x: x.x500))

    # def save_json(self, filepath):
    #     with open(filepath, 'wb') as fp:
    #         obj = {'students': {sid: student.obj for sid, student in self.students.items()},
    #                'groups': self.groups,
    #                'group_submitters': self.}
    #         json.dump()

    def get_not_done(self):
        return filter(lambda x: not x.done, self.students.values())

    def get_student_id_by_name(self, fname, lname, ignore_case=True):
        for sid, student in self.students.items():
            if ignore_case:
                if student.fname.lower() == fname.lower() and student.lname.lower() == lname.lower():
                    return sid
            else:
                if student.fname == fname and student.lname == lname:
                    return sid
        return None

    def get_student_id_by_external_id(self, external_id):
        for sid, student in self.students.items():
            if student.external_id == external_id:
                return sid
        return None

    def load_groups(self, filename: str):
        self.groups = []  # type: List[StudentGroup]
        with open(filename, "r") as fp:
            obj = json.load(fp)
        for group in obj:
            students = [self.students[sid] for sid in group]
            self.groups += [StudentGroup(students)]

    def load(self, f):
        roster_reader = csv.DictReader(f)
        for row in roster_reader:
            try:
                sid = row["Id"].strip().replace("@umn.edu", "")
            except KeyError:
                raise Exception("Row was {}".format(row))
            score = int(row["Score"].strip())
            comments = row["Comments"]
            self.students[sid].score = score
            self.students[sid].comment = comments

    def dump_moodle(self, f):
        writer = csv.DictWriter(f, ['Id', 'Score', 'Comments'])
        writer.writeheader()
        for student in sorted(self, key=lambda x: x.x500):
            row = {"Id": "{}@umn.edu".format(student.x500),
                   "Score": student.score,
                   "Comments": student.comment}
            if not student.score:
                row["Score"] = 0
            writer.writerow(row)

    def dump_canvas(self, f):
        writer = csv.DictWriter(f, ['Student Name', 'ID', 'SIS Login ID', 'Section', 'Score'])
        writer.writeheader()
        for student in sorted(self, key=lambda x: x.x500):
            row = {"Student Name": student.fname + " " + student.lname,
                   "ID": student.external_id,
                   "SIS Login ID": "{}@umn.edu".format(student.x500),
                   "Section": 1,
                   "Score": student.score}
            if not student.score:
                row["Score"] = 0
            writer.writerow(row)

    def dump(self, f, format: OutputFormat = OutputFormat.MOODLE):
        if format == OutputFormat.MOODLE:
            return self.dump_moodle(f)
        elif format == OutputFormat.CANVAS:
            return self.dump_canvas(f)
        raise ValueError(f'Invalid format: {format}')

    def dumps(self, format: OutputFormat = OutputFormat.MOODLE):
        f = io.StringIO()
        self.dump(f, format)
        return f.getvalue()

    def export_grades(self, filepath, format: OutputFormat = OutputFormat.MOODLE):
        with open(filepath, "w") as fp:
            self.dump(fp, format)
