import argparse
import os
import time
from multiprocessing.pool import Pool

from grading_lib import Roster, extract_moodle_zip
from grading_lib.interface import WebGrader


class GradingError(Exception):
    def __init__(self, student_x500, message):
        self.x500 = student_x500
        self.message = message

    def __str__(self):
        return "{} for {}: {}".format(self.__class__.__name__, self.x500, self.message)


class FetchError(GradingError):
    pass


class InvalidSubmissionError(GradingError):
    pass


# TODO: Add grading warnings.

class Grader(object):
    """ Grading Pipeline:
          - `fetch`
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

    def fetch_student(self, student):
        pass

    def pre_grade(self):
        """This function runs first before any other function
        """

    def pre_grade_student(self, student):
        pass

    def grade_student(self, student):
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

        if args.verbose:
            self.VERBOSE = True

        if args.manual:
            self.manual_grade()
            return

        self.roster = Roster(args.roster)
        if args.serve:
            WebGrader(self).run()
            return

        if args.student:  # If we only want a single student then replace the list of students with the single one.
            self.roster.students = {args.student: self.roster.students[args.student]}

        start_time = time.time()

        if args.fetch:
            print("Fetching...")
            self.fetch()

            def do_fetch(student):
                try:
                    self.fetch_student(student)
                except FetchError as e:
                    student.done = True
                    student.add_cmt("{} (credit: 0/100)".format(e.message))
            list(self.map(do_fetch, self.roster))

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

        if args.save_output:
            self.roster.export_grades(os.path.join(self.OUT_DIR, "{}_grades.csv".format(int(start_time))))
        else:
            print(self.roster.dumps())

        end_time = time.time()
        print("Took {} seconds.".format(int(end_time - start_time)))
        print("Remember to run using the '-m' option to finish the grading.")


class MoodleBasedGrader(Grader):
    EXTRACT_SUBMISSION = False

    def fetch(self):
        if not os.path.exists("moodle_dump"):
            os.mkdir("moodle_dump")
        input("Make sure you download submissions zip to 'moodle_dump'")
        moodle_zip = os.listdir("moodle_dump")[0]
        assert moodle_zip.endswith(".zip"), "Moodle archive must be a zip file."

    # def pre_grade(self):
    #     moodle_zip = os.listdir("moodle_dump")[0]
        extract_moodle_zip("moodle_dump/" + moodle_zip, "input", "tmp", self.roster, internal_tarball=self.EXTRACT_SUBMISSION)
