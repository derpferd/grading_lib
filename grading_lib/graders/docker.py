#!/usr/bin/python3
import os
import re
from abc import abstractmethod
from pathlib import Path
from subprocess import CompletedProcess
from typing import List

from grading_lib.writeup import Priority
from .base import Grader
from .. import Question, Writeup
from ..docker import DockerRunner, DockerTimeoutException
from ..roster import Student


class SimpleDockerGrader(Grader):
    @staticmethod
    @abstractmethod
    def docker_image_name() -> str:
        ...

    @staticmethod
    @abstractmethod
    def sources() -> List[str]:
        ...

    @staticmethod
    def docker_image_build_dir() -> str:
        return 'testing_img'

    @staticmethod
    def docker_timeout_sec() -> int:
        return 60

    @staticmethod
    def docker_disk_cap_mb() -> int:
        return 100

    @classmethod
    def source_paths(cls, student: Student) -> List[Path]:
        return [Path("repos", student.x500, file) for file in cls.sources()]

    @classmethod
    def pre_grade(cls):
        if cls.VERBOSE:
            print("Creating docker image...")
        DockerRunner.build_docker_image(cls.docker_image_name(), cls.docker_image_build_dir())

        super().pre_grade()

    @classmethod
    def grade_student(cls, student: Student):
        if cls.VERBOSE:
            print("Grading {}...".format(student.x500))
        student.score = 0
        writeup = Writeup()

        cls.grade_code(student, writeup)
        cls.add_sections_to_write_up(student, writeup)

        writeup.save(os.path.join(cls.write_ups_dir(), student.x500))

    @classmethod
    def grade_code(cls, student: Student, writeup: Writeup):
        grader = DockerRunner(cls.docker_image_name(), default_timeout=cls.docker_timeout_sec())
        grader.MAX_DISK = f'{cls.docker_disk_cap_mb()}m'

        if cls.repo_for(student).is_branchless:
            student.add_cmt(Question('repo', 100, "Couldn't find repository.").get_msg(0))
            return

        for path in cls.source_paths(student):
            if not path.exists():
                student.add_cmt(Question(path.name, 100, f"Couldn't find {path.name}").get_msg(0))
                return

        try:
            result = grader.run({path: path.name for path in cls.source_paths(student)})
        except DockerTimeoutException:
            student.add_cmt("Program timed out (credit 0/100)")
            return

        writeup.add_section("Test output",
                            Priority.Info - 1,
                            f"exit code: '{result.returncode}'\n"
                            f"stdout: '{result.stdout.decode('utf-8')}'\n"
                            f"stderr: '{result.stderr.decode('utf-8')}'")

        if result.returncode:  # non zero exit code
            if result.returncode == 2:
                student.add_cmt("Compile Error (credit 0/100)")
            else:
                student.add_cmt(f"Error with code {result.returncode} (credit 0/100)")
            return

        test_counts = re.findall(b'You passed ([0-9]{1,5}) out of ([0-9]{1,5})', result.stdout)

        assert len(test_counts) == 1
        test_correct, test_total = map(int, test_counts[0])
        student.score = (test_correct * 100) // test_total

    @classmethod
    def add_sections_to_write_up(cls, student: Student, writeup: Writeup):
        super().add_sections_to_write_up(student, writeup)
        writeup.add_section("Grades", Priority.Error, text="Grade so far: {}\nFeedback: {}".format(student.score, student.comment))

        for source_path in cls.source_paths(student):
            source_code = f'No {source_path.name} found :('
            if os.path.exists(source_path):
                source_code = open(str(source_path), 'r').read()

            writeup.add_section(source_path.name, Priority.Debug + 1, source_code)

    @abstractmethod
    def process_output(self, student: Student, result: CompletedProcess):
        """This function should add comments and the score to the student based on the result."""
        ...
