import os
from flask import Flask, request, render_template, redirect
from ..question import GradeDB
app = Flask(__name__)


class Data:
    gradedb = None
    grader = None


@app.route('/')
def index():
    if Data.grader is None:
        return redirect("/grade")
    return render_template('index.html', lab_name="Lab 2", roster=Data.grader.roster)


@app.route('/merge', methods=["GET", "POST"])
def merge():
    if request.method == 'POST':
        src = request.form.get("src")
        origin = request.form.get("origin")

        try:
            Data.gradedb.merge(src)
            return redirect(origin)
        except:
            return "There was an error :("
    else:
        origin = request.form.get("origin", "/grade")
        files = os.listdir("output")
        files = map(lambda x: os.path.abspath("output/"+x), files)
        files = list(filter(os.path.isfile, files))
        return render_template('merge.html', files=files, origin=origin)


@app.route('/grade', methods=["GET", "POST"])
def grade():
    message = ""
    if request.method == 'POST':
        x500 = request.form.get("x500")
        grades = {}
        for question in Data.gradedb.questions:
            grades[question.name] = int(request.form.get(question.name))
        # request.form.get('pass')
        if x500 and len(grades) == len(Data.gradedb.questions):
            for name, grade in grades.items():
                Data.gradedb.set_grade(x500, name, grade)
            message = "Set grades for {}".format(x500)
        else:
            message = "Error setting grades for {}".format(x500)
        action = request.form.get('action', 'save')
        if action == 'save':
            save()
        elif action == 'save_next':
            save()
            i = 0
            rows = Data.gradedb.get_rows()
            while rows[i].x500 != x500:
                i += 1
            i += 1
            if i < len(rows):
                return redirect("/grade/{}".format(rows[i].x500))
        # print("Got:", grades, "for", x500)
        # message =
    return render_template('grade.html', lab_name="Lab 2", rows=Data.gradedb.get_rows(), message=message)


@app.route('/grade/<x500>')
def grade_student(x500):
    return render_template('grade_student.html', questions=Data.gradedb.questions, x500=x500, writeup=Data.gradedb.get_writeup(x500),
                           grades=Data.gradedb.get_grades(x500))


@app.route('/save')
def save():
    Data.gradedb.save()
    return "Saved"


@app.route('/kill')
def kill():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return "Shutting down..."


if __name__ == '__main__':
    app.run()


class WebQuestionGrader:
    def __init__(self, questions, writeup_dir, save_loc):
        self.questions = questions
        self.writeup_dir = writeup_dir
        self.save_loc = save_loc

    def grade(self):
        """Returns True if finished grading otherwise False"""
        Data.gradedb = GradeDB(self.questions, self.writeup_dir, self.save_loc)
        app.run()
        return False

    def load(self):
        raise DeprecationWarning("No need to call this.")


class WebGrader:
    def __init__(self, grader):
        Data.grader = grader

    def run(self):
        Data.gradedb = GradeDB(Data.grader.manual_questions, Data.grader.write_ups_dir, Data.grader.save_loc)
        app.run()
