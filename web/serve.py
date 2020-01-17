from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, current_user, login_user, login_required, logout_user
from flask_bootstrap import Bootstrap
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import MultiDict
from werkzeug.security import generate_password_hash, check_password_hash
import os
import glob
import re
import importlib
from web.forms import CodeSumitForm, LoginForm, UploadForm, AddSeminar
import timeit
import random
import string

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
    results = db.relationship('Result', backref='user', lazy=True)
    seminars = db.relationship('Seminar', secondary='access')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String)
    passed_num = db.Column(db.Integer)
    runtime = db.Column(db.Float)
    success = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)

class Seminar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seminar_num = db.Column(db.Integer)
    registration = db.Column(db.String)
    sessions = db.relationship('Session', backref='seminar', lazy=True)
    users = db.relationship('User', secondary='access')

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_num = db.Column(db.Float)
    entry_point = db.Column(db.String)
    runtime = db.Column(db.Float)
    blacklist = db.Column(db.String)
    seminar_id = db.Column(db.Integer, db.ForeignKey('seminar.id'), nullable=False)
    results = db.relationship('Result', backref='session', lazy=True)

    def get_blacklist(self):
        return list(filter(lambda x: x != '', self.blacklist.split(',')))

class Access(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seminar_id = db.Column(db.Integer, db.ForeignKey('seminar.id'), nullable=False)

    user = db.relationship('User', backref=db.backref("seminar", cascade="all, delete-orphan"))
    seminar = db.relationship('Seminar', backref=db.backref("user", cascade="all, delete-orphan"))

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

# add example user, seminar and session
db.create_all()
example_admin = User(id=1, email="example_admin_user@gmail.com", is_admin=True)
example_admin.set_password("111")
db.session.merge(example_admin)

example_user = User(id=2, email="example_user@gmail.com", is_admin=False)
example_user.set_password("111")
db.session.merge(example_user)

example_seminar = Seminar(id=1, seminar_num=156, registration="join156")
db.session.merge(example_seminar)

example_session = Session(id = 1, session_num=1.1, seminar_id=1, entry_point="entry", runtime=1.0, blacklist='')
db.session.merge(example_session)
db.session.commit()

# index page shows a list of all available seminars
@app.route('/', methods=["GET", "POST"])
@login_required
def index():
    if current_user.is_admin:
        seminars = sorted(Seminar.query.all(), key = lambda x: x.seminar_num)
    else:
        seminars = sorted(Seminar.query.filter(Seminar.users.any(id=current_user.id)).all(), key = lambda x: x.seminar_num)
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

    if not current_user.is_admin and not any(int(seminar_num) == i.seminar_num for i in current_user.seminars):
        flash('You have no access to this course!')
        return redirect(url_for('index'))

    form = CodeSumitForm()

    # list available sessions
    available = Session.query.filter(Session.seminar.has(seminar_num=seminar_num)).all()
    form.sessions.choices = sorted([(i.session_num, 'session %s' % i.session_num) for i in available])

    if request.method == "POST":
        if is_valid(form.filename.data.filename):

            filename = secure_filename(form.filename.data.filename)
            form.filename.data.save(os.path.join(app.config["FILE_UPLOADS"], filename))

            # import test cases
            try:
                i1, i2 = str(form.sessions.data).split('.')
            except:
                i1 = str(form.sessions.data)
                i2 = 0
                
            test_cases = importlib.import_module('.session_%s_%s' % (i1, i2), 'web.tests.%s' % str(seminar_num))
            content = []

            # read in student submission
            with open(os.path.join(app.config["FILE_UPLOADS"], filename), 'r') as file:
                for line in file:
                    content.append(line)
            to_test = ''.join(content)

            # fetch session settings
            setting = Session.query.filter(Session.seminar.has(seminar_num=seminar_num)).filter_by(session_num=form.sessions.data).first()
            temp = test_cases.TestCases(to_test)
            res = temp.test(runtime = setting.runtime, entry_point = setting.entry_point, blacklist = setting.get_blacklist())

            # record runtime
            time = timeit.timeit(lambda: test_cases.TestCases(to_test).test(runtime = setting.runtime, entry_point = setting.entry_point, blacklist = setting.get_blacklist()), number = 1)

            # remove submission
            os.remove(os.path.join(app.config["FILE_UPLOADS"], filename))

            passed_num = sum([1 for case in res if res[case] == "Passed"])
            to_add = Result(user_id = current_user.id, email = current_user.email, session_id=setting.id, passed_num=passed_num, runtime = time, success = passed_num == len(temp.answers))
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

        seminar_id = Seminar.query.filter_by(seminar_num=form.seminar_num.data).first().id
        to_add = {'seminar_id': seminar_id, 'entry_point': form.entry_point.data, 'runtime': form.runtime.data, 'blacklist': form.blacklist.data, 'session_num': form.session_num.data}

        # update / insert session settings
        if Session.query.filter_by(seminar_id=seminar_id, session_num=form.session_num.data).first():
            s = Session.query.filter_by(seminar_id=seminar_id, session_num=form.session_num.data).first()
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

    random_generated = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(6))
    form = AddSeminar(formdata=MultiDict({'registration_link': random_generated}))

    if request.method == "POST":

        form = AddSeminar()
        if Seminar.query.filter_by(seminar_num=form.seminar_num.data).first() is None:
            new_seminar = Seminar(seminar_num=form.seminar_num.data, registration=form.registration_link.data)
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
    seminar = Seminar.query.all()
    return render_template('all_setting.html', seminar = seminar)

@app.route('/all_settings/<seminar_id>')
@login_required
def session_settings(seminar_id):
    if not current_user.is_admin: return redirect('/')
    session = Session.query.filter_by(seminar_id=seminar_id).all()

    total_s = len(Seminar.query.filter_by(id=seminar_id).first().users)

    for ind in range(len(session)):
        session[ind].submitted_students = len(set([t.user.id for t in session[ind].results]))

        if session[ind].submitted_students != 0:
            session[ind].passing_rate = len(set([t.user.id for t in session[ind].results if t.success ])) / float(session[ind].submitted_students)
        else:
            session[ind].passing_rate = 0

    return render_template('session_settings.html', session = session)

@app.route('/register/<link>', methods=["GET", "POST"])
@login_required
def register(link):

    if current_user.is_admin:
        flash('You are an admin! Enjoy your privileges.')
        return redirect(url_for('index'))

    res = Seminar.query.filter_by(registration=link).first()
    if not res:
        flash('The registration link does not exist!')
        return redirect(url_for('index'))

    if any(user.id == current_user.id for user in res.users):
        flash('You have already registered!')
        return redirect(url_for('index'))

    db.session.add(Access(user_id=current_user.id, seminar_id=res.id))
    db.session.commit()

    flash('You have successfully registered!')
    return redirect(url_for('index'))

@app.route('/delete_course/<seminar_id>')
@login_required
def delete_course(seminar_id):
    if not current_user.is_admin: return redirect('/')

    seminar = Seminar.query.filter_by(id=seminar_id).first()
    if not seminar:
        flash('Course to delete does not exist')
        return redirect(url_for('all_settings'))
    else:
        os.remove(os.path.join(app.config["SESSION_UPLOADS"], seminar.seminar_num))
        db.session.delete(seminar)
        db.session.commit()
        return redirect(url_for('all_settings'))

@app.route('/delete_session/<session_id>')
@login_required
def delete_session(session_id):
    if not current_user.is_admin: return redirect('/')

    session = Session.query.filter_by(id=session_id).first()
    if not session:
        flash('Session to delete does not exist')
        return redirect(url_for('/'))
    else:

        i1, i2 = str(session.session_num).split('.')
        valid_name = 'session_%s_%s.py' % (i1, i2)

        os.remove(os.path.join(app.config["SESSION_UPLOADS"], str(session.seminar.seminar_num), valid_name))
        db.session.delete(session)
        db.session.commit()
        return redirect(url_for('all_settings'))

if __name__ == '__main__':
    app.run()
