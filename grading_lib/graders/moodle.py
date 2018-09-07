import os

from .base import Grader
from .. import extract_moodle_zip


class MoodleBasedGrader(Grader):
    EXTRACT_SUBMISSION = False

    def fetch(self):
        if not os.path.exists("moodle_dump"):
            os.mkdir("moodle_dump")
        input("Make sure you download submissions zip to 'moodle_dump'")
        moodle_zip = os.listdir("moodle_dump")[0]
        assert moodle_zip.endswith(".zip"), "Moodle archive must be a zip file."

    def pre_grade(self):
        moodle_zip = os.listdir("moodle_dump")[0]
        extract_moodle_zip("moodle_dump/" + moodle_zip, "input", "tmp", self.roster, internal_tarball=self.EXTRACT_SUBMISSION)
