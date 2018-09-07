import os
from functools import lru_cache
from typing import List

from git import GitCommandError

from .base import Grader
from .errors import *
from .. import GitRepo, Writeup
from ..roster import Student


class GitBasedGrader(Grader):
    GIT_REPO_URL: str  # ex. "git@github.umn.edu:{}/lab_name.git" Note: '{}' will be replaced by the student's x500.
    GIT_LAST_NON_STUDENT_COMMIT: str  # A hash of the last commit made before the students started.
    GIT_EXCLUDE = None  # an optional list of excludes for all git commands like diff and log.

    def __init__(self):
        super().__init__()
        assert self.GIT_REPO_URL != "", "You must set a git repo url"

    @lru_cache()
    def repo_for(self, student):
        return GitRepo(student.x500, self.GIT_REPO_URL.format(student.x500), cache_dir="repos")

    def fetch_student(self, student):
        if self.VERBOSE:
            print("Pulling {}...".format(student))
        repo = self.repo_for(student)
        try:
            repo.pull()
        except:  # TODO: Fix this except to only catch the correct errors.
            repo.remove()
            raise FetchError(student.x500, "{}'s repo is non-existent or you don't have access permissions.".format(student.x500))
        return repo

    def get_submitting_student(self, group: List[Student]) -> Student:
        submitting_student = None
        submitting_student_repo = None
        for student in group:
            if os.path.exists(os.path.join("repos", student.x500)):
                if submitting_student is None:
                    submitting_student = student
                    submitting_student_repo = self.repo_for(student)
                else:
                    print("Multiple students submitted. :(")
                    if self.repo_for(student).commit().authored_date > submitting_student_repo.commit().authored_date:
                        # This one is newer
                        submitting_student = student
                        submitting_student_repo = self.repo_for(student)
                    print("\tSelected {}'s".format(submitting_student))
        if submitting_student is None:
            raise GroupFetchError([x.x500 for x in group], "No student in group submitted. :(")
        return submitting_student

    def get_git_start_and_end(self, student: Student):
        repo = self.repo_for(student)

        start = end = None
        try:
            start = repo.commit(self.GIT_LAST_NON_STUDENT_COMMIT)
        except:
            pass
        try:
            end = repo.commit()
        except:
            pass

        return start, end

    def add_git_diff_section(self, student: Student, writeup: Writeup):
        start, end = self.get_git_start_and_end(student=student)
        repo = self.repo_for(student)

        text = "Invalid Git Repo"
        html = None

        if start and end and start != end:
            text = repo.diff(start, end, exclude=self.GIT_EXCLUDE)
            html = repo.html_diff(start, end, exclude=self.GIT_EXCLUDE)

        writeup.add_section("Git Diff", text=text, html=html)

    def add_git_log_section(self, student: Student, writeup: Writeup):
        start, end = self.get_git_start_and_end(student=student)
        repo = self.repo_for(student)

        try:
            text = repo.log()
            html = repo.html_log()
        except GitCommandError:
            text = "Invalid Git Repo"
            html = None

        if start and end and start != end:
            text = repo.log(start, end)
            html = repo.html_log(start, end)

        writeup.add_section("Git Log", text=text, html=html)
