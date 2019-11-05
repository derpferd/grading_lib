import argparse
import os
import time

from . import Roster
from .graders.base import Grader
from .graders.errors import *
from .interface.web.server import WebGrader


# self.pool = None  # type:Pool
# if self.THREAD_SAFE:
#     self.pool = Pool(os.cpu_count())
#     self.map = self.pool.map
# else:
#     self.map = map


def run(grader: Grader):
    """This will parse command line args and run needed steps."""

    print('honk')
    parser = argparse.ArgumentParser()
    if grader.GROUP_BASED:
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
    if grader.GROUP_BASED:
        assert os.path.exists(args.groups) and os.path.isfile(
            args.groups), "Invalid group file: '{}' does not exist or isn't a file".format(args.groups)

    if args.verbose:
        grader.VERBOSE = True

    if args.manual:
        grader.manual_grade()
        return

    grader.roster = Roster(args.roster)
    if grader.GROUP_BASED:
        grader.roster.load_groups(args.groups)

    if args.serve:
        WebGrader(grader).run()
        return

    if args.student:  # If we only want a single student then replace the list of students with the single one.
        __all_students = grader.roster.students
        grader.roster.students = {args.student: grader.roster.students[args.student]}

    start_time = time.time()

    if args.fetch:
        print("Pre fetching...")
        grader.pre_fetch()
        print("Fetching...")
        grader.fetch()

        def do_fetch(student):
            try:
                grader.fetch_student(student)
            except FetchError as ex:
                student.done = True
                student.add_cmt("{} (credit: 0/100)".format(ex.message))

        list(grader.map(do_fetch, grader.roster))

    if grader.GROUP_BASED:
        if args.student:
            for group in grader.roster.groups:
                student = __all_students[args.student]
                if student in group:
                    grader.roster.groups = [group]
                    break

        for group in grader.roster.groups:
            try:
                grader.roster.group_submitters[grader.get_submitting_student(group)] = group
            except GroupFetchError as e:
                student = grader.roster.students[e.x500]
                grader.roster.group_submitters[student] = group
                student.done = True
                student.add_cmt("{} (credit: 0/100)".format(e.message))

        grader.roster.students = {student.x500: student for student in grader.roster.group_submitters}

    grader.pre_grade()

    def do_pre_grade(student):
        try:
            grader.pre_grade_student(student)
        except InvalidSubmissionError as e:
            student.done = True
            student.add_cmt("{} (credit: 0/100)".format(e.message))

    list(grader.map(do_pre_grade, grader.roster.get_not_done()))

    def do_grade(student):
        grader.grade_student(student)

    list(grader.map(do_grade, grader.roster.get_not_done()))

    grader.post_grade()

    if grader.GROUP_BASED:
        for submitter, group in grader.roster.group_submitters.items():
            for student in group:
                student.score = submitter.score
                student.comment = submitter.comment
                grader.roster.students[student.x500] = student

    if args.save_output:
        grader.roster.export_grades(os.path.join(grader.OUT_DIR, "{}_grades.csv".format(int(start_time))))
    else:
        print(grader.roster.dumps())

    end_time = time.time()
    print("Took {} seconds.".format(int(end_time - start_time)))
    print("Remember to run using the '-m' option to finish the grading.")
