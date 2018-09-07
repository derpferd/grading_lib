import argparse
import os
import time
from contextlib import suppress
from multiprocessing.pool import Pool
from typing import List

from .errors import *
from ..interface import WebGrader
from ..roster import Student, Roster


class Grader(object):
    """ Grading Pipeline:
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
    THREAD_SAFE = False  # by default assume not thread safe.
    VERBOSE = False
    GROUP_BASED = False

    OUT_DIR = "output"

    def __init__(self):
        self.roster = None  # type:Roster
        self.pool = None  # type:Pool
        if self.THREAD_SAFE:
            self.pool = Pool(os.cpu_count())
            self.map = self.pool.map
        else:
            self.map = map
        if not os.path.exists(self.OUT_DIR):
            os.mkdir(self.OUT_DIR)

    def fetch(self):
        pass

    def get_submitting_student(self, group: List[Student]) -> Student:
        raise NotImplemented()

    def fetch_student(self, student):
        pass

    def pre_grade(self):
        """This function runs first before any other grading function
        """
        with suppress(OSError):
            os.mkdir(self.write_ups_dir)

    def pre_grade_student(self, student):
        """

        Args:
            student:

        Raises:
            InvalidSubmissionError if the student's submission is invalid
        """
        pass

    def grade_student(self, student: Student):
        pass

    def post_grade(self):
        """This function should clean up any temporary files created by the pre_grade and grade steps. Note: this should leave the fetch data intacted"""
        pass

    def manual_grade(self):
        """This function should ask for any information needed from a human grader to finish grading the assignments.
        This function should save it's work as it goes and recover if called again.
        """
        pass

    @property
    def manual_questions(self):
        return []

    @property
    def write_ups_dir(self):
        return os.path.join(self.OUT_DIR, "writeups")

    @property
    def save_loc(self):
        return os.path.join(self.OUT_DIR, "q_grading.sav")

    def main(self):
        """This will parse command line args and run needed steps."""
        parser = argparse.ArgumentParser()
        if self.GROUP_BASED:
            parser.add_argument("-g", "--groups", help="The filepath of the file containing the groups", type=str,
                                default="groups.json")
        parser.add_argument("-s", "--student", help="only grade a student by their x500", nargs="?", type=str)
        parser.add_argument("-r", "--roster", help="The filepath of the roster to use.", nargs="?", type=str,
                            default="../roster.csv")
        parser.add_argument("-o", "--save-output", help="Save the grades to the output directory", action="store_true")
        parser.add_argument("-f", "--fetch", help="Run fetch step", action="store_true")
        parser.add_argument("-m", "--manual", help="Do the manual part of the grading.", action="store_true")
        parser.add_argument("-v", "--verbose", help="Print Debug", action="store_true")
        parser.add_argument("--serve", help="Start server.", action="store_true")
        args = parser.parse_args()

        assert os.path.exists(args.roster) and os.path.isfile(
            args.roster), "Invalid roster file: '{}' does not exist or isn't a file".format(args.roster)
        if self.GROUP_BASED:
            assert os.path.exists(args.groups) and os.path.isfile(
            args.groups), "Invalid group file: '{}' does not exist or isn't a file".format(args.groups)

        if args.verbose:
            self.VERBOSE = True

        if args.manual:
            self.manual_grade()
            return

        self.roster = Roster(args.roster)
        if self.GROUP_BASED:
            self.roster.load_groups(args.groups)

        if args.serve:
            WebGrader(self).run()
            return

        if args.student:  # If we only want a single student then replace the list of students with the single one.
            __all_students = self.roster.students
            self.roster.students = {args.student: self.roster.students[args.student]}

        start_time = time.time()

        if args.fetch:
            print("Fetching...")
            self.fetch()

            def do_fetch(student):
                try:
                    self.fetch_student(student)
                except FetchError as ex:
                    student.done = True
                    student.add_cmt("{} (credit: 0/100)".format(ex.message))
            list(self.map(do_fetch, self.roster))

        if self.GROUP_BASED:
            if args.student:
                for group in self.roster.groups:
                    student = __all_students[args.student]
                    if student in group:
                        self.roster.groups = [group]
                        break

            for group in self.roster.groups:
                try:
                    self.roster.group_submitters[self.get_submitting_student(group)] = group
                except GroupFetchError as e:
                    student = self.roster.students[e.x500]
                    self.roster.group_submitters[student] = group
                    student.done = True
                    student.add_cmt("{} (credit: 0/100)".format(e.message))

            self.roster.students = {student.x500: student for student in self.roster.group_submitters}

        self.pre_grade()

        def do_pre_grade(student):
            try:
                self.pre_grade_student(student)
            except InvalidSubmissionError as e:
                student.done = True
                student.add_cmt("{} (credit: 0/100)".format(e.message))
        list(self.map(do_pre_grade, self.roster.get_not_done()))

        def do_grade(student):
            self.grade_student(student)
        list(self.map(do_grade, self.roster.get_not_done()))

        self.post_grade()

        if self.GROUP_BASED:
            for submitter, group in self.roster.group_submitters.items():
                for student in group:
                    student.score = submitter.score
                    student.comment = submitter.comment
                    self.roster.students[student.x500] = student

        if args.save_output:
            self.roster.export_grades(os.path.join(self.OUT_DIR, "{}_grades.csv".format(int(start_time))))
        else:
            print(self.roster.dumps())

        end_time = time.time()
        print("Took {} seconds.".format(int(end_time - start_time)))
        print("Remember to run using the '-m' option to finish the grading.")

