import os

from grading_lib.roster import OutputFormat
from .base import Grader
from .. import extract_canvas_zip


class CanvaseGrader(Grader):
    EXTRACT_SUBMISSION = False

    def fetch(self):
        if not os.path.exists("canvas_dump"):
            os.mkdir("canvas_dump")
        input("Make sure you download submissions zip to 'canvas_dump'")
        canvas_zip = os.listdir("canvas_dump")[0]
        assert canvas_zip.endswith(".zip"), "Canvas archive must be a zip file."

        extract_canvas_zip("canvas_dump/" + canvas_zip, "input", "tmp", self.roster, internal_tarball=self.EXTRACT_SUBMISSION)

    @classmethod
    def fetch_student(cls, student):
        pass

    def export_grades(self, output_file):
        self.roster.export_grades(output_file, OutputFormat.CANVAS)
