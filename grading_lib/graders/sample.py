import os

from .base import Grader
from ..question import PartialCreditQuestion
from ..question import QuestionGrader


class FullyAutoGrader(Grader):
    @property
    def manual_questions(self):
        return [PartialCreditQuestion("Added Partial Credit", "Partial Credit")] + super().manual_questions

    def manual_grade(self):
        grader = QuestionGrader(self.manual_questions, self.write_ups_dir())
        grader.grade()
