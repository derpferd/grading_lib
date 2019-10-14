import os
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import List, ClassVar

from grading_lib import Question, Writeup
from grading_lib.db.groups import GroupsDB
from grading_lib.db.question import ReviewDB
from grading_lib.db.student import StudentDB
from .errors import FetchError, InvalidSubmissionError
from ..roster import Student, Roster


class Grader(ABC):
    """ Grading Pipeline:
          - `pre_fetch`
          - `fetch`
          - If group_based: `get_submitting_student(group)`
          - for each student
            - `fetch_student`
          - `pre_grade`
          - for each student
            - `pre_grade_student`
          - for each student
            - `grade_student`
          - `post_grade`

        The reason to have fetch separate from pre_grade is so that we could pull a repo once. etc...
    """
    FETCH_THREADS = 1  # by default assume not thread safe.
    PRE_GRADE_THREADS = 1  # by default assume not thread safe.
    GRADE_THREADS = 1  # by default assume not thread safe.
    VERBOSE = False
    GROUP_BASED: ClassVar[bool] = False

    OUT_DIR = 'output'
    DATA_DIR = 'data'

    def __init__(self, roster: Roster):
        self.roster = roster
        if not os.path.exists(self.OUT_DIR):
            os.mkdir(self.OUT_DIR)
        if not os.path.exists(self.DATA_DIR):
            os.mkdir(self.DATA_DIR)

    def pre_fetch(self):
        pass

    @classmethod
    @abstractmethod
    def fetch(self):
        pass

    def get_submitting_student(self, group: List[Student]) -> Student:
        raise NotImplemented()

    @classmethod
    @abstractmethod
    def fetch_student(cls, student):
        pass

    @classmethod
    def pre_grade(cls):
        """This function runs first before any other grading function
        """
        with suppress(OSError):
            os.mkdir(cls.write_ups_dir())

    @classmethod
    def pre_grade_student(cls, student):
        """

        Args:
            student:

        Raises:
            InvalidSubmissionError if the student's submission is invalid
        """
        pass

    @classmethod
    @abstractmethod
    def grade_student(cls, student: Student):
        pass

    @classmethod
    def post_grade(cls):
        """This function should clean up any temporary files created by the pre_grade and grade steps. Note: this should leave the fetch data intacted"""
        pass

    @abstractmethod
    def manual_grade(self):
        """This function should ask for any information needed from a human grader to finish grading the assignments.
        This function should save it's work as it goes and recover if called again.
        """
        pass

    def export_grades(self, output_file):
        self.roster.export_grades(output_file)

    @property
    def manual_questions(self) -> List[Question]:
        return []

    @classmethod
    def add_sections_to_write_up(cls, student: Student, writeup: Writeup):
        ...

    @classmethod
    def write_ups_dir(cls):
        return os.path.join(cls.OUT_DIR, "writeups")

    @property
    def save_loc(self):
        return os.path.join(self.OUT_DIR, "q_grading.sav")

    @classmethod
    def main(cls):
        from ..interface import cli
        cli.run(cls)

    @classmethod
    def fetch_student_wrapper(cls, student: Student):
        print(f'Fetching student: {student.x500}')
        try:
            cls.fetch_student(student)
        except FetchError as ex:
            student.done = True
            student.add_cmt("{} (credit: 0/100)".format(ex.message))
        cls.fetch_db().save(student)

    @classmethod
    def pre_grade_student_wrapper(cls, student: Student):
        if not student.done:
            try:
                cls.pre_grade_student(student)
            except InvalidSubmissionError as e:
                student.done = True
                student.add_cmt("{} (credit: 0/100)".format(e.message))
        cls.grade_db().save(student)

    @classmethod
    def grade_wrapper(cls, student: Student):
        if not student.done:
            print(f'Grading {student.x500}...')
            cls.grade_student(student)
        cls.grade_db().save(student)

    @classmethod
    def fetch_db(cls) -> StudentDB:
        return StudentDB(os.path.join(cls.DATA_DIR, 'fetch'))

    @classmethod
    def grade_db(cls) -> StudentDB:
        return StudentDB(os.path.join(cls.DATA_DIR, 'grade'))

    @classmethod
    def review_db(cls) -> ReviewDB:
        return ReviewDB(os.path.join(cls.DATA_DIR, 'review'))

    @classmethod
    def group_db(cls) -> GroupsDB:
        return GroupsDB(os.path.join(cls.DATA_DIR, 'groups'))

    # def main(self):
    #     """This will parse command line args and run needed steps."""
    #     parser = argparse.ArgumentParser()
    #     if self.GROUP_BASED:
    #         parser.add_argument("-g", "--groups", help="The filepath of the file containing the groups", type=str,
    #                             default="groups.json")
    #     parser.add_argument("-s", "--student", help="only grade a student by their x500", nargs="?", type=str)
    #     parser.add_argument("-r", "--roster", help="The filepath of the roster to use.", nargs="?", type=str,
    #                         default="../roster.csv")
    #     parser.add_argument("-o", "--save-output", help="Save the grades to the output directory", action="store_true")
    #     parser.add_argument("-f", "--fetch", help="Run fetch step", action="store_true")
    #     parser.add_argument("-m", "--manual", help="Do the manual part of the grading.", action="store_true")
    #     parser.add_argument("-v", "--verbose", help="Print Debug", action="store_true")
    #     parser.add_argument("--serve", help="Start server.", action="store_true")
    #     args = parser.parse_args()
    #
    #     assert os.path.exists(args.roster) and os.path.isfile(
    #         args.roster), "Invalid roster file: '{}' does not exist or isn't a file".format(args.roster)
    #     if self.GROUP_BASED:
    #         assert os.path.exists(args.groups) and os.path.isfile(
    #         args.groups), "Invalid group file: '{}' does not exist or isn't a file".format(args.groups)
    #
    #     if args.verbose:
    #         self.VERBOSE = True
    #
    #     if args.manual:
    #         self.manual_grade()
    #         return
    #
    #     self.roster = Roster(args.roster)
    #     if self.GROUP_BASED:
    #         self.roster.load_groups(args.groups)
    #
    #     if args.serve:
    #         WebGrader(self).run()
    #         return
    #
    #     if args.student:  # If we only want a single student then replace the list of students with the single one.
    #         __all_students = self.roster.students
    #         self.roster.students = {args.student: self.roster.students[args.student]}
    #
    #     start_time = time.time()
    #
    #     if args.fetch:
    #         print("Fetching...")
    #         self.fetch()
    #
    #         def do_fetch(student):
    #             try:
    #                 self.fetch_student(student)
    #             except FetchError as ex:
    #                 student.done = True
    #                 student.add_cmt("{} (credit: 0/100)".format(ex.message))
    #         list(self.map(do_fetch, self.roster))
    #
    #     if self.GROUP_BASED:
    #         if args.student:
    #             for group in self.roster.groups:
    #                 student = __all_students[args.student]
    #                 if student in group:
    #                     self.roster.groups = [group]
    #                     break
    #
    #         for group in self.roster.groups:
    #             try:
    #                 self.roster.group_submitters[self.get_submitting_student(group)] = group
    #             except GroupFetchError as e:
    #                 student = self.roster.students[e.x500]
    #                 self.roster.group_submitters[student] = group
    #                 student.done = True
    #                 student.add_cmt("{} (credit: 0/100)".format(e.message))
    #
    #         self.roster.students = {student.x500: student for student in self.roster.group_submitters}
    #
    #     self.pre_grade()
    #
    #     def do_pre_grade(student):
    #         try:
    #             self.pre_grade_student(student)
    #         except InvalidSubmissionError as e:
    #             student.done = True
    #             student.add_cmt("{} (credit: 0/100)".format(e.message))
    #     list(self.map(do_pre_grade, self.roster.get_not_done()))
    #
    #     def do_grade(student):
    #         self.grade_student(student)
    #     list(self.map(do_grade, self.roster.get_not_done()))
    #
    #     self.post_grade()
    #
    #     if self.GROUP_BASED:
    #         for submitter, group in self.roster.group_submitters.items():
    #             for student in group:
    #                 student.score = submitter.score
    #                 student.comment = submitter.comment
    #                 self.roster.students[student.x500] = student
    #
    #     if args.save_output:
    #         self.roster.export_grades(os.path.join(self.OUT_DIR, "{}_grades.csv".format(int(start_time))))
    #     else:
    #         print(self.roster.dumps())
    #
    #     end_time = time.time()
    #     print("Took {} seconds.".format(int(end_time - start_time)))
    #     print("Remember to run using the '-m' option to finish the grading.")
