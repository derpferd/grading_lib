import os
from multiprocessing import Pool
from typing import Type, Dict

import click

from grading_lib.db.student import StudentGroup
from .web import WebGrader
from ..graders.base import Grader
from ..graders.errors import GroupFetchError
from ..roster import Roster, Student


class Context:
    grader: Grader
    student: str = None
    all_students: Dict[str, Student] = None


def process_groups(context: Context):
    grader = context.grader
    if context.student:  # if we are focused on a single student make sure we get their group.
        for group in grader.roster.groups:
            student = context.all_students[context.student]
            if student in group:
                grader.roster.groups = [group]
                break

    for group in grader.roster.groups:
        try:
            submitter = grader.get_submitting_student(group).x500
        except GroupFetchError as e:
            submitter = e.x500
            student = grader.fetch_db().get(submitter)
            student.done = True
            student.add_cmt("{} (credit: 0/100)".format(e.message))
            grader.fetch_db().save(student)

        new_group = StudentGroup(submitter, [s.x500 for s in group])
        grader.group_db().save(new_group)

    # grader.roster.students = {student.x500: student for student in grader.roster.group_submitters}


def run(grader_cls: Type[Grader]):
    context = Context()

    @click.option('-s', '--student', type=str, help='Perform work on a single student by their x500')
    @click.option('-r', '--roster', default='../roster.csv', type=click.Path(exists=True),
                  help='The filepath of the roster to use.')
    @click.option('-v', '--verbose', is_flag=True, help='Print Debug')
    def cli(student, roster, verbose, groups=None):
        """This is the command line interface for Jonathan's automatic grading system.

        To properly grade the students work make sure to run the commands in the following order.

            \b
            1. fetch
            2. grade
            3. review
            4. export

        For more help about a specific step run `command --help`.

        """
        grader = grader_cls(Roster(roster))
        grader.VERBOSE = verbose
        if grader.GROUP_BASED:
            grader.roster.load_groups(groups)

        if student:  # If we only want a single student then replace the list of students with the single one.
            context.student = student
            context.all_students = grader.roster.students
            grader.roster.students = {student: grader.roster.students[student]}

        context.grader = grader

    if grader_cls.GROUP_BASED:
        cli = click.option('-g', '--groups', default='groups.json', type=click.Path(exists=True),
                           help='The filepath of the file containing the groups')(cli)
    cli = click.group()(cli)

    @cli.command(short_help="Fetch students submissions.")
    def fetch():
        """This prepares the students' submissions grading.
        Depending on the type of submission this could mean downloading the repositories from github or extracting the
        zip file from Moodle.

        """
        grader = context.grader
        print("Pre fetching...")
        grader.pre_fetch()
        print("Fetching...")
        grader_cls.fetch()

        with Pool(grader_cls.FETCH_THREADS) as pool:
            pool.map(grader_cls.fetch_student_wrapper, grader.roster)

        if grader_cls.GROUP_BASED:
            process_groups(context)  # TODO: test this

        print("Done fetching.")

    @cli.command(short_help="Grade students submissions.")
    def grade():
        """This actually grades the student's work.
        """
        grader = context.grader

        if context.student and grader.GROUP_BASED:
            group = grader.group_db().get(context.student)
            if not group:
                raise Exception(f'Could find group for: {context.student}')
            context.student = group.submitter

        fetched_students = grader.fetch_db().students.values()

        if context.student:
            fetched_students = [grader.fetch_db().get(context.student)]

        grader.pre_grade()

        with Pool(grader_cls.PRE_GRADE_THREADS) as pool:
            pool.map(grader_cls.pre_grade_student_wrapper, fetched_students)

        with Pool(grader_cls.GRADE_THREADS) as pool:
            pool.map(grader_cls.grade_wrapper, fetched_students)

        grader.post_grade()

        if grader.GROUP_BASED:
            for group in grader.group_db().groups.values():
                submitter = grader.grade_db().get(group.submitter)
                for member in group.members:
                    if not member == group.submitter:
                        student = grader.roster.students[member]
                        student.score = submitter.score
                        student.comment = submitter.comment
                        grader.grade_db().save(student)

    @cli.command(short_help="Review students submissions.")
    def review():
        """This opens an interface where the grader can grade the part of the assignment that need a human's touch.
        This could be partial credit or written questions.

        Currently this feature isn't implemented. Please add partial credit manually.
        """
        context.grader.manual_grade()
        # raise NotImplemented("This feature is not currently implemented.")

    @cli.command(short_help="Export the students' grades to a csv file.")
    @click.option('-o', '--output-file', default='grades.csv', type=click.Path(),
                  help='Path to the file to output. Should end in .csv')
    def export(output_file):
        """Puts all of the saved information together and export the students' grades and grading comments to a csv
        file.
        """
        if os.path.exists(output_file):
            ans = ''
            while ans not in ['y', 'n']:
                ans = input(f"File {output_file} already exists. You are sure you want to override it [Y/N]? ").lower()
            if ans == 'n':
                print("Exiting...")
                exit(0)
            print("Overwriting...")

        assert context.student is None, "Exporting single student's grade isn't currently supported."

        for x500, student in grader_cls.grade_db().students.items():
            s = context.grader.roster.students[x500]
            s.score = student.score
            s.comment = student.comment

            review_rec = grader_cls.review_db().get(x500)
            s.score += review_rec.score
            for question in context.grader.manual_questions:
                s.add_cmt(question.get_msg(review_rec.get(question.name)))

        context.grader.roster.export_grades(output_file)

    @cli.command(short_help="Start the server (To be implemented)")
    def serve():
        """This serves a local web server that allows the grader a have a nice web interface instead of a cli.
        This feature is yet to be implemented.
        """
        raise NotImplemented("This feature is not currently implemented.")
        WebGrader(context.grader).run()

    cli(obj={})
