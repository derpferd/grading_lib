import sys
assert sys.version_info.major >= 3 and sys.version_info.minor >= 5, "Only Python >= 3.5 supported"

from grading_lib.git import GitRepo
from grading_lib.roster import Roster
from grading_lib.zip import extract_moodle_zip
from grading_lib.dir import check_if_dir_contains_files
from grading_lib.question import Question, QuestionGrader, PartialCreditQuestion
from grading_lib.grader import Grader
from grading_lib.interface import WebQuestionGrader
from grading_lib.writeup import Writeup
