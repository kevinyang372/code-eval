from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, current_user, login_user, login_required, logout_user
from flask_bootstrap import Bootstrap
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import glob
import re
import importlib
from web.forms import CodeSumitForm, LoginForm, UploadForm, AddSeminar
import timeit

import sys
sys.path.append('web/tests')

app = Flask(__name__)

app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["FILE_UPLOADS"] = "web/tmp"
app.config["SESSION_UPLOADS"] = "web/tests"
app.config["ALLOWED_EXTENSIONS"] = ["py", "ipynb"]

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
bootstrap = Bootstrap(app)
login.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200))
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    email = db.Column(db.String)
    seminar_num = db.Column(db.Integer)
    session = db.Column(db.Float)
    passed_num = db.Column(db.Integer)
    runtime = db.Column(db.Float)

class Seminar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seminar_num = db.Column(db.Integer)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_num = db.Column(db.Float)
    seminar_num = db.Column(db.Integer)
    entry_point = db.Column(db.String)
    runtime = db.Column(db.Float)
    blacklist = db.Column(db.String)

    def get_blacklist(self):
        return list(filter(lambda x: x != '', self.blacklist.split(',')))

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

# add example user, seminar and session
db.create_all()
example_user = User(id=1, email="example_admin_user@gmail.com", is_admin=True)
example_user.set_password("111")
db.session.merge(example_user)

example_seminar = Seminar(id=1, seminar_num=156)
db.session.merge(example_seminar)

example_session = Session(id = 1, session_num=1.1, seminar_num=156, entry_point="entry", runtime=1.0, blacklist='')
db.session.merge(example_session)
db.session.commit()

# index page shows a list of all available seminars
@app.route('/', methods=["GET", "POST"])
@login_required
def index():
    seminars = sorted(Seminar.query.all(), key = lambda x: x.seminar_num)
    return render_template('index.html', seminars = seminars)

# submission page
@app.route('/seminars/<seminar_num>', methods=["GET", "POST"])
@login_required
def seminar(seminar_num):

    # check if filename is valid
    def is_valid(filename):
        if filename and '.' in filename and filename.split('.')[1] in app.config["ALLOWED_EXTENSIONS"]:
            return True
        return False

    form = CodeSumitForm()

    # list available sessions
    available = Session.query.filter_by(seminar_num=seminar_num).all()
    form.sessions.choices = sorted([(i.session_num, 'session %s' % i.session_num) for i in available])

    if request.method == "POST":
        if is_valid(form.filename.data.filename):

            filename = secure_filename(form.filename.data.filename)
            form.filename.data.save(os.path.join(app.config["FILE_UPLOADS"], filename))

            # import test cases
            i1, i2 = str(form.sessions.data).split('.')
            test_cases = importlib.import_module('.session_%s_%s' % (i1, i2), 'web.tests.%s' % str(seminar_num))
            content = []

            # read in student submission
            with open(os.path.join(app.config["FILE_UPLOADS"], filename), 'r') as file:
                for line in file:
                    content.append(line)
            to_test = ''.join(content)

            # fetch session settings
            setting = Session.query.filter_by(seminar_num=seminar_num, session_num=form.sessions.data).first()
            temp = test_cases.TestCases(to_test)
            res = temp.test(runtime = setting.runtime, entry_point = setting.entry_point, blacklist = setting.get_blacklist())

            # record runtime
            time = timeit.timeit(lambda: test_cases.TestCases(to_test).test(runtime = setting.runtime, entry_point = setting.entry_point, blacklist = setting.get_blacklist()), number = 1)

            # remove submission
            os.remove(os.path.join(app.config["FILE_UPLOADS"], filename))

            passed_num = sum([1 for case in res if res[case] == "Passed"])
            to_add = Result(user_id = current_user.id, email = current_user.email, session=form.sessions.data, passed_num=passed_num, runtime = time, seminar_num = seminar_num)
            db.session.add(to_add)
            db.session.commit()

            return render_template('results.html', result = res, passed = passed_num, total = len(temp.answers), file = content, time = time)

        return redirect(request.url)

    return render_template('seminars.html', form = form)

@app.route('/summary')
@login_required
def summary():
    if not current_user.is_admin: return redirect('/')
    results = Result.query.all()
    return render_template('summary.html', result = results)

@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated: return redirect('/')

    form = LoginForm()
    if request.method == "POST":
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        return redirect('/')
    return render_template('login.html', form = form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

@app.route('/upload_session', methods=["GET", "POST"])
@login_required
def upload_session():

    if not current_user.is_admin: return redirect('/')

    form = UploadForm()
    form.seminar_num.choices = sorted([(s.seminar_num, 'seminar %s' % str(s.seminar_num)) for s in Seminar.query.all()])

    if request.method == "POST":

        filename = secure_filename(form.filename.data.filename)
        i1, i2 = str(form.session_num.data).split('.')
        valid_name = 'session_%s_%s.py' % (i1, i2)

        if os.path.exists(os.path.join(app.config["SESSION_UPLOADS"], form.seminar_num.data, valid_name)):
            os.remove(os.path.join(app.config["SESSION_UPLOADS"], form.seminar_num.data, valid_name))

        form.filename.data.save(os.path.join(app.config["SESSION_UPLOADS"], form.seminar_num.data, filename))
        os.rename(os.path.join(app.config["SESSION_UPLOADS"], form.seminar_num.data, filename), os.path.join(app.config["SESSION_UPLOADS"], form.seminar_num.data, valid_name))

        to_add = {'seminar_num': form.seminar_num.data, 'entry_point': form.entry_point.data, 'runtime': form.runtime.data, 'blacklist': form.blacklist.data, 'session_num': form.session_num.data}

        # update / insert session settings
        if Session.query.filter_by(seminar_num=form.seminar_num.data, session_num=form.session_num.data).first():
            s = Session.query.filter_by(seminar_num=form.seminar_num.data, session_num=form.session_num.data).first()
            for key, val in to_add.items():
                setattr(s, key, val)
        else:
            s = Session(**to_add)
            db.session.add(s)

        db.session.commit()
        return redirect('/')

        return redirect(request.url)

    return render_template('upload_session.html', form = form)

@app.route('/add_seminar', methods=["GET", "POST"])
@login_required
def add_seminar():

    if not current_user.is_admin: return redirect('/')

    form = AddSeminar()
    if request.method == "POST":

        if Seminar.query.filter_by(seminar_num=form.seminar_num.data).first() is None:
            new_seminar = Seminar(seminar_num=form.seminar_num.data)
            db.session.add(new_seminar)
            db.session.commit()

            path = os.path.join(app.config["SESSION_UPLOADS"], str(form.seminar_num.data))
            os.mkdir(path)
        else:
            flash('Seminar already exists')
            return redirect(url_for('add_seminar'))

        return redirect('/')

    return render_template('add_seminar.html', form = form)

@app.route('/all_settings')
@login_required
def all_settings():
    if not current_user.is_admin: return redirect('/')
    session = Session.query.all()
    return render_template('all_setting.html', session = session)

if __name__ == '__main__':
    app.run()
