from __future__ import print_function
import csv
import io


class Student(object):
    def __init__(self, x500, fname, lname):
        self.x500 = x500
        self.fname = fname
        self.lname = lname
        self.score = None
        self.comment = ""

    def get_name(self, sep=" ", reverse=False):
        name = [self.fname, self.lname]
        if reverse:
            name.reverse()
        return sep.join(name)

    def add_comment(self, s):
        if s.strip():
            self.comment += s.rstrip() + "  "

    def add_cmt(self, s):
        self.add_comment(s)

    def __str__(self):
        return "<Student {}>".format(self.x500)


class Roster(object):
    def __init__(self, roster_path="../roster.csv"):
        self.roster_path = roster_path
        self.students = {}
        self.__load_roster()

    def __load_roster(self):
        self.students = {}
        with open(self.roster_path, 'r', newline='') as fp:
            roster_reader = csv.DictReader(fp)
            for row in roster_reader:
                sid = row["x500"].strip()
                fname = row["first name"].strip()
                lname = row["last name"].strip()
                self.students[sid] = Student(sid, fname, lname)

    def __iter__(self):
        return iter(sorted(self.students.values(), key=lambda x: x.x500))

    def get_student_id_by_name(self, fname, lname, ignore_case=True):
        for sid, student in self.students.items():
            if ignore_case:
                if student.fname.lower() == fname.lower() and student.lname.lower() == lname.lower():
                    return sid
            else:
                if student.fname == fname and student.lname == lname:
                    return sid
        return None

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

    def dump(self, f):
        writer = csv.DictWriter(f, ['Id', 'Score', 'Comments'])
        writer.writeheader()
        for student in sorted(self, key=lambda x: x.x500):
            row = {"Id": "{}@umn.edu".format(student.x500),
                   "Score": student.score,
                   "Comments": student.comment}
            if not student.score:
                row["Score"] = 0
            writer.writerow(row)
        # s = "Id, Score, Comments\n"
        # for student in sorted(self, key=lambda x: x.x500):
        #     if student.score:
        #         s += "{}@umn.edu, {}, \"{}\"\n".format(student.x500, student.score, student.comment)
        #     else:
        #         s += "{}@umn.edu, 0, \"{}\"\n".format(student.x500, student.comment)
        # return s

    def dumps(self):
        f = io.StringIO()
        self.dump(f)
        return f.getvalue()

    def export_grades(self, filepath):
        with open(filepath, "w") as fp:
            self.dump(fp)
        # # TODO: use csv lib to export
        # with open(filepath, "w") as fp:
        #     fp.write("Id, Score, Comments\n")
        #     for student in sorted(self, key=lambda x: x.x500):
        #         if student.score:
        #             fp.write("{}@umn.edu, {}, \"{}\"\n".format(student.x500, student.score, student.comment))
        #         else:
        #             fp.write("{}@umn.edu, 0, \"{}\"\n".format(student.x500, student.comment))
        #             if print_unset:
        #                 print("{} has no grade".format(student.x500))
