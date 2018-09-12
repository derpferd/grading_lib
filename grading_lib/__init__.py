import sys

assert sys.version_info.major >= 3 and sys.version_info.minor >= 6, "Only Python >= 3.6 supported"

from grading_lib.git import GitRepo
from grading_lib.roster import Roster
from grading_lib.zip import extract_moodle_zip
from grading_lib.dir import check_if_dir_contains_files
from grading_lib.question import Question, QuestionGrader, PartialCreditQuestion
from grading_lib.interface.web import WebQuestionGrader, WebGrader
from grading_lib.writeup import Writeup
from grading_lib.interface import cli

from grading_lib.graders.errors import *
from grading_lib.graders.base import Grader
from grading_lib.graders.docker import SimpleDockerGrader
from grading_lib.graders.git import GitGrader
from grading_lib.graders.moodle import MoodleGrader
from grading_lib.graders.sample import FullyAutoGrader
