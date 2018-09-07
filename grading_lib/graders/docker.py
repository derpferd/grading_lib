#!/usr/bin/python3
import os
import re
from abc import abstractmethod
from pathlib import Path
from subprocess import CompletedProcess
from typing import List

from .git import GitBasedGrader
from .. import Question, Writeup, PartialCreditQuestion, QuestionGrader
from ..docker import DockerGrader, DockerTimeoutException
from ..roster import Student


class SimpleDockerGitGrader(GitBasedGrader):
    GIT_REPO_URL = 'git@github.umn.edu:{}/vigenere.git'
    GIT_LAST_NON_STUDENT_COMMIT = '2fda232'
    GIT_EXCLUDE = ['DECODED/*', 'ENCODED/*']

    DOCKER_IMAGE_NAME = 'umd_cs_4821_vigenere'
    DOCKER_IMAGE_BUILD_DIR = 'testing_img'

    THREAD_SAFE = False
    GROUP_BASED = False

    VERBOSE = True
    TIMEOUT_SEC = None  # Defaults to 60 sec

    SOURCES: list

    def __init__(self):
        assert getattr(self, "SOURCES", None), "SOURCES is not set"
        assert isinstance(getattr(self, "SOURCES"), list), "SOURCES must be a list"

        super().__init__()

    def source_paths(self, student: Student) -> List[Path]:
        return [Path("repos", student.x500, file) for file in self.SOURCES]

    def pre_grade(self):
        if self.VERBOSE:
            print("Creating docker image...")
        DockerGrader.build_docker_image(self.DOCKER_IMAGE_NAME, self.DOCKER_IMAGE_BUILD_DIR)

        super().pre_grade()

    def grade_student(self, student: Student):
        if self.VERBOSE:
            print("Grading {}...".format(student.x500))
        student.score = 0
        grading_writeup = Writeup()

        self.grade_code(student, grading_writeup)
        writeup = self.create_write_up(student, grading_writeup)

        writeup.save(os.path.join(self.write_ups_dir, student.x500))

    def grade_code(self, student: Student, writeup: Writeup):
        grader = DockerGrader(self.DOCKER_IMAGE_NAME, default_timeout=self.TIMEOUT_SEC)

        if self.repo_for(student).is_branchless:
            student.add_cmt(Question('repo', 100, "Couldn't find repository.").get_msg(0))
            return

        for path in self.source_paths(student):
            if not path.exists():
                student.add_cmt(Question(path.name, 100, f"Couldn't find {path.name}").get_msg(0))
                return

        try:
            result = grader.run({path: path.name for path in self.source_paths(student)})
        except DockerTimeoutException:
            student.add_cmt("Program timed out (credit 0/100)")
            return

        writeup.add_section("Test output",
                            f"exit code: '{result.returncode}'\n"
                            f"stdout: '{result.stdout.decode('utf-8')}'\n"
                            f"stderr: '{result.stderr.decode('utf-8')}'")

        if result.returncode:  # non zero exit code
            if result.returncode == 2:
                student.add_cmt("Compile Error (credit 0/100)")
            else:
                student.add_cmt(f"Error with code {result.returncode} (credit 0/100)")
            return

        test_counts = re.findall(b'You passed ([0-9]{1,3}) out of ([0-9]{1,3})', result.stdout)

        assert len(test_counts) == 1
        test_correct, test_total = map(int, test_counts[0])
        student.score = (test_correct * 100) // test_total

    def create_write_up(self, student, grading_writeup):
        writeup = Writeup()
        writeup.add_section("Grades", text="Grade so far: {}\nFeedback: {}".format(student.score, student.comment))
        writeup += grading_writeup
        self.add_git_diff_section(student, writeup)
        self.add_git_log_section(student, writeup)

        for source_path in self.source_paths(student):
            source_code = f'No {source_path.name} found :('
            if os.path.exists(source_path):
                source_code = open(str(source_path), 'r').read()

            writeup.add_section(source_path.name, source_code)

        return writeup

    @property
    def manual_questions(self):
        return [PartialCreditQuestion("Added Partial Credit", "Partial Credit")]

    def manual_grade(self):
        grader = QuestionGrader(self.manual_questions, self.write_ups_dir, os.path.join(self.OUT_DIR, "q_grading.sav"))
        grader.grade()

    @abstractmethod
    def process_output(self, student: Student, result: CompletedProcess):
        """This function should add comments and the score to the student based on the result."""
        ...
