import os
from abc import abstractmethod
from functools import lru_cache
from typing import List

from git import GitCommandError

from grading_lib.writeup import Priority
from .base import Grader
from .errors import *
from .. import GitRepo, Writeup
from ..roster import Student


class GitGrader(Grader):
    FETCH_THREADS = 32  # We can have lots of threads since most of the time we are waiting on the network.

    @staticmethod
    @abstractmethod
    def git_repo_url(x500: str) -> str:
        ...

    @staticmethod
    @abstractmethod
    def git_last_non_student_commit() -> str:
        """Should return a hash of the last commit made before the students started."""
        ...

    @staticmethod
    def git_exclude() -> List[str]:
        """list of excludes for all git commands like diff and log."""
        return []

    @staticmethod
    @abstractmethod
    def sources() -> List[str]:
        ...

    @classmethod
    @lru_cache()
    def repo_for(cls, student):
        return GitRepo(student.x500, cls.git_repo_url(student.x500), cache_dir="repos")

    @classmethod
    def fetch(cls):
        pass

    @classmethod
    def fetch_student(cls, student):
        if cls.VERBOSE:
            print("Pulling {}...".format(student))
        repo = cls.repo_for(student)
        try:
            repo.pull()
        except:  # TODO: Fix this except to only catch the correct errors.
            repo.remove()
            raise FetchError(student.x500, "{}'s repo is non-existent or you don't have access permissions.".format(student.x500))
        return repo

    @classmethod
    def get_submitting_student(cls, group: List[Student]) -> Student:
        submitting_student = None
        submitting_student_repo = None
        for student in group:
            if os.path.exists(os.path.join("repos", student.x500)):
                if submitting_student is None:
                    submitting_student = student
                    submitting_student_repo = cls.repo_for(student)
                else:
                    print("Multiple students submitted. :(")
                    if self.repo_for(student).commit().authored_date > submitting_student_repo.commit().authored_date:
                        # This one is newer
                        submitting_student = student
                        submitting_student_repo = cls.repo_for(student)
                    print("\tSelected {}'s".format(submitting_student))
        if submitting_student is None:
            raise GroupFetchError([x.x500 for x in group], "No student in group submitted. :(")
        return submitting_student

    @classmethod
    def get_git_start_and_end(cls, student: Student):
        repo = cls.repo_for(student)

        start = end = None
        try:
            start = repo.commit(cls.git_last_non_student_commit())
        except:
            pass
        try:
            end = repo.commit()
        except:
            pass

        return start, end

    @classmethod
    def add_git_diff_section(cls, student: Student, writeup: Writeup):
        start, end = cls.get_git_start_and_end(student=student)
        repo = cls.repo_for(student)

        text = "Invalid Git Repo"
        html = None

        if start and end and start != end:
            text = repo.diff(start, end, exclude=cls.git_exclude())
            html = repo.html_diff(start, end, exclude=cls.git_exclude())

        writeup.add_section("Git Diff", Priority.Debug - 1, text=text, html=html)

    @classmethod
    def add_git_log_section(cls, student: Student, writeup: Writeup):
        start, end = cls.get_git_start_and_end(student=student)
        repo = cls.repo_for(student)

        try:
            text = repo.log()
            html = repo.html_log()
        except GitCommandError:
            text = "Invalid Git Repo"
            html = None

        if start and end and start != end:
            text = repo.log(start, end)
            html = repo.html_log(start, end)

        writeup.add_section("Git Log", Priority.Debug, text=text, html=html)

    @classmethod
    def add_sections_to_write_up(cls, student: Student, writeup: Writeup):
        cls.add_git_diff_section(student, writeup)
        cls.add_git_log_section(student, writeup)
