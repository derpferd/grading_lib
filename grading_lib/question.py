import json
import os
import time
from collections import namedtuple

from grading_lib import npyscreen
from grading_lib.db.question import ReviewDB

log = open("log.log", "w")


class Question(object):
    def __init__(self, name, points, incorrect_msg, help_text=""):
        self.name = name
        self.points = points
        self.incorrect_msg = incorrect_msg
        self.help_text = help_text

    def get_msg(self, points, custom_message=None):
        if points == self.points:
            return ""
        else:
            msg = self.incorrect_msg
            if custom_message:
                msg = custom_message
            return "{} (credit: {}/{})".format(msg, points, self.points)


class PartialCreditQuestion(Question):
    def __init__(self, name, msg=None, help_text=""):
        super().__init__(name, 100, msg, help_text)

    def get_msg(self, points, custom_message=None):
        if points == 0:
            return ""
        else:
            msg = self.incorrect_msg
            if custom_message:
                msg = custom_message
            return "{} (credit: +{})".format(msg, points)


class Writeup(object):
    def __init__(self):
        self.sections = []

    def add_section(self, title, text):
        self.sections += [{"title": title, "text": text}]

    def dump(self, fp):
        for section in self.sections:
            fp.write("======= {} =======\n".format(section["title"]))
            fp.write(section["text"])
            fp.write("\n\n")


class GradeDB(object):
    Row = namedtuple("Row", ["x500", "score", "msg"])

    def __init__(self, questions, writeup_dir, root):
        self.questions = questions
        self.writeup_dir = writeup_dir
        self.root = root

        self.students = []
        self.grades = {}
        self.questions_by_name = {}

        self.db = ReviewDB(root)
        self.__load_or_init()

    def __load_or_init(self):
        for question in self.questions:
            self.questions_by_name[question.name] = question

        # Add any non added students
        for writeup in sorted(os.listdir(self.writeup_dir)):
            name = os.path.splitext(writeup)[0]
            if name not in self.students:
                self.students += [name]

        self.students.sort()

    def get_rows(self):
        return [self.Row(name, self.db.get(name).score, self.get_msg_for(name)) for name in self.students]

    def get_grade(self, name: str, question: str) -> int:
        return self.db.get(name).get(question)

    def set_grade(self, x500, q_name, grade):
        rec = self.db.get(x500)
        rec.set(q_name, grade)
        self.db.save(rec)

    def get_msg_for(self, name):
        msgs = []
        for question in self.questions:
            msgs += [question.get_msg(self.get_grade(name, question.name))]
        return "  ".join(msgs)

    def get_text_for(self, value):
        name = value
        return open(os.path.join(self.writeup_dir, name + ".txt"), "rb").read().decode("utf-8", "ignore")

    def get_writeup(self, x500):
        return json.load(open(os.path.join(self.writeup_dir, x500 + ".json"), "r"))


class QuestionGrader(object):
    def __init__(self, questions, writeup_dir, save_loc='data/review'):
        self.questions = questions
        self.writeup_dir = writeup_dir
        self.save_loc = save_loc

    def grade(self):
        """Returns True if finished grading otherwise False"""
        # for writeup in sorted(os.listdir(self.writeup_dir)):
        #     print(writeup)
        self.gradedb = GradeDB(self.questions, self.writeup_dir, self.save_loc)
        myApp = AddressBookApplication(self.gradedb)
        myApp.run()
        return False

    def load(self):
        raise DeprecationWarning("No need to call this.")


# GUI code
class RecordList(npyscreen.MultiLineAction):
    def __init__(self, *args, **keywords):
        super(RecordList, self).__init__(*args, **keywords)
        self.add_handlers({
            # "^S": self.when_merge,
            "^D": self.when_save,
        })

    def display_value(self, vl):
        return "{}, {}: {}".format(vl[0], str(vl[1]).rjust(3), vl[2])

    def actionHighlighted(self, act_on_this, keypress):
        self.parent.parentApp.getForm('EDITRECORDFM').value = act_on_this[0]
        self.parent.parentApp.switchForm('EDITRECORDFM')

    # def when_merge(self, *args, **keywords):
    #     # notify_result = npyscreen.notify_ok_cancel("You want to merge?", title='popup')
    #     # npyscreen.notify("File: {}".format(the_selected_file), title='Merging')
    #     # time.sleep(2)
    #     # if notify_result:
    #     the_selected_file = npyscreen.selectFile()
    #     npyscreen.notify("Merging grades into {} now...".format(the_selected_file), title='Merging')
    #     self.parent.parentApp.gradedb.merge(the_selected_file)
    #     npyscreen.notify("Finished merging in grades", title='Merged')
    #     time.sleep(1)
    #     # else:
    #     #     npyscreen.notify("Didn't merge", title='Not Merged')
    #     #     time.sleep(.5)

    def when_save(self, *args, **keywords):
        the_selected_file = npyscreen.selectFile()
        npyscreen.notify("Saving grades to {} now...".format(the_selected_file), title='Saving')
        self.parent.parentApp.gradedb.save_as(the_selected_file)
        npyscreen.notify("Finished saving in grades", title='Saved')
        time.sleep(1)


class RecordListDisplay(npyscreen.FormBaseNew):
    FRAMED = False

    def create(self):
        self.list = self.add(RecordList, name="Test")

    def beforeEditing(self):
        self.update_list()

    def update_list(self):
        self.list.values = self.parentApp.gradedb.get_rows()
        self.list.display()


class EditRecord(npyscreen.ActionForm):
    def create(self):
        self.add_handlers({
            "^X": self.when_save,
            "^S": self.when_save,
            "^A": self.when_exit,
        })
        self.value = None
        # self.questions = self.add(npyscreen.BoxBasic, name="Questions:", max_width=30, relx=2, max_height=3)
        # self.wgLastName = self.add(npyscreen.TitleText, name = "Last Name:",)
        self.questions = {}
        for question in self.parentApp.gradedb.questions:
            self.questions[question.name] = self.add(TitleNumber, name="{}:".format(question.name), value="", total=str(question.points), relx=3, max_width=30)

        # self.writeup = self.add(npyscreen.Pager, name="Writeup", rely=2, relx=33)
        self.writeup = self.add(npyscreen.Pager, name="Writeup", rely=2, relx=34, autowrap=True, exit_left=True, exit_right=True)
        # self.writeup.values = ["This is a test"]
        # self.writeup = self.add(npyscreen.BoxTitle, name="Writeup:", rely=2, relx=32)
        # self.wgOtherNames = self.add(npyscreen.TitleText, name = "Other Names:")
        # self.wgEmail      = self.add(npyscreen.TitleText, name = "Email:")

    def beforeEditing(self):
        if self.value:
            record = self.parentApp.gradedb.get_text_for(self.value)
            self.name = "Grading for %s" % self.value
            self.writeup.values = record.split("\n")
            for q_name in self.parentApp.gradedb.questions_by_name.keys():
                grade = self.parentApp.gradedb.get_grade(self.value, q_name)
                if grade == 0:
                    self.questions[q_name].value = ""
                else:
                    self.questions[q_name].value = str(grade)
            # grades = self.parentApp.gradedb.get_grades(self.value)
            # for q_name, grade in grades.items():
            # self.record_id          = record[0]
            # self.wgLastName.value   = record[1]
            # self.wgOtherNames.value = record[2]
            # self.wgEmail.value      = record[3]
        else:
            self.parentApp.switchFormPrevious()
        # else:
        #     self.name = "New Record"
        #     self.record_id          = ''
        #     self.wgLastName.value   = ''
        #     self.wgOtherNames.value = ''
        #     self.wgEmail.value      = ''

    def when_save(self, *args, **keywords):
        self.on_ok()

    def when_exit(self, *args, **keywords):
        self.parentApp.setNextForm(None)
        self.on_cancel()

    def on_ok(self):
        # grades = [int("0" + x.value) for x in self.questions]
        for q_name, question in self.questions.items():
            self.parentApp.gradedb.set_grade(self.value, q_name, int("0" + question.value))
        # self.parentApp.gradedb.save()

        # if self.record_id: # We are editing an existing record
        #     self.parentApp.gradedb.update_record(self.record_id,
        #                                     last_name=self.wgLastName.value,
        #                                     other_names = self.wgOtherNames.value,
        #                                     email_address = self.wgEmail.value,
        #                                     )
        # else: # We are adding a new record.
        #     self.parentApp.gradedb.add_record(last_name=self.wgLastName.value,
        #     other_names = self.wgOtherNames.value,
        #     email_address = self.wgEmail.value,
        #     )
        self.parentApp.switchFormPrevious()

    def on_cancel(self):
        self.parentApp.switchFormPrevious()


class AddressBookApplication(npyscreen.NPSAppManaged):
    def __init__(self, gradedb):
        super().__init__()
        self.gradedb = gradedb

    def onStart(self):
        log.write("Starting")
        self.addForm("MAIN", RecordListDisplay)
        self.addForm("EDITRECORDFM", EditRecord)


class NumberEntry(npyscreen.Textfield):
    def __init__(self, screen, total=None, *args, **kwargs):
        super().__init__(screen, *args, **kwargs)
        self.total = total
        log.write("\nT: {} id:{}\n".format(self.total, id(self)))
        log.write("\nB: {}\n".format(hasattr(self, "total")))

    def _print(self):
        # log.write("\nC: {}\n".format(hasattr(self, "total")))
        # if hasattr(self, "total"):
        #     log.write("\nD: {}\n".format(self.total))
        # log.write("\nA: {} id:{}".format(self.value, self.total))
        # if isinstance(self.value, tuple):
        #     self.value, self.total = self.value
        if hasattr(self, "total"):
            num_str = "{}/{}".format(self.value, self.total)
        else:
            num_str = "{}".format(self.value)
        # num_str = "{}/{}".format(self.value, self.total)
        strlen = len(num_str)
        if self.maximum_string_length < strlen:
            tmp_x = self.relx
            for i in range(self.maximum_string_length):
                self.parent.curses_pad.addch(self.rely, tmp_x, num_str[i])
                tmp_x += 1

        else:
            tmp_x = self.relx
            for i in range(strlen):
                self.parent.curses_pad.addch(self.rely, tmp_x, num_str[i])
                # self.parent.curses_pad.addstr(self.rely, tmp_x, '-')
                tmp_x += 1

    def when_value_edited(self):
        if not self.value.isdigit():
            self.value = "".join([c for c in self.value if c.isdigit()])
        while hasattr(self, "total") and int("0" + self.value) > int(self.total):
            self.value = self.value[:-1]


class TitleNumber(npyscreen.TitleText):
    _entry_type = NumberEntry
