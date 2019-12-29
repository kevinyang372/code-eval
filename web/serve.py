from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import glob
import re
import importlib
from web.forms import CodeSumitForm

app = Flask(__name__)

app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["FILE_UPLOADS"] = "/Users/kevin/desktop/Github/codeEval/web/tmp"
app.config["ALLOWED_EXTENSIONS"] = ["py", "ipynb"]
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))

db.create_all()
example_user = User(name="Philip Sterne")
db.session.merge(example_user)
db.session.commit()

@app.route('/', methods=["GET", "POST"])
def index():

    def is_valid(filename):
        if filename and '.' in filename and filename.split('.')[1] in app.config["ALLOWED_EXTENSIONS"]:
            return True
        return False

    form = CodeSumitForm()

    total = glob.glob('web/tests/session_*.py')
    pattern = re.compile('web/tests/session_(.*).py')
    form.sessions.choices = [(i + 1, 'session %s' % pattern.findall(v)[0]) for i, v in enumerate(list(filter(pattern.match, total)))]

    if request.method == "POST":
        if is_valid(form.filename.data.filename):

            filename = secure_filename(form.filename.data.filename)
            form.filename.data.save(os.path.join(app.config["FILE_UPLOADS"], filename))

            test_cases = importlib.import_module('.session_%s' % form.sessions.data, 'web.tests')
            to_test = importlib.import_module('.' + filename.split('.')[0], 'web.tmp')

            temp = test_cases.TestCases(to_test.entry)
            res = temp.test()

            os.remove(os.path.join(app.config["FILE_UPLOADS"], filename))
            return render_template('results.html', result = res, total = len(temp.answers))

        return redirect(request.url)

    return render_template('index.html', form = form)

@app.route('/results')
def results():
    return render_template('results.html', result = {}, total = 0)

if __name__ == '__main__':
    app.run()
