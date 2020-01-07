from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, current_user, login_user, login_required, logout_user
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import glob
import re
import importlib
from web.forms import CodeSumitForm, LoginForm, UploadForm
import timeit

import sys
sys.path.append('web/tests')

app = Flask(__name__)

app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["FILE_UPLOADS"] = "/Users/kevin/desktop/Github/codeEval/web/tmp"
app.config["SESSION_UPLOADS"] = "/Users/kevin/desktop/Github/codeEval/web/tests"
app.config["ALLOWED_EXTENSIONS"] = ["py", "ipynb"]

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
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

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

db.create_all()
example_user = User(email="example_admin_user@gmail.com", is_admin = True)
example_user.set_password("111") 
db.session.merge(example_user)
db.session.commit()

@app.route('/', methods=["GET", "POST"])
@login_required
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
            to_test = ''

            with open(os.path.join('web/tmp', filename), 'r') as file:
                for line in file:
                    to_test += line

            temp = test_cases.TestCases(to_test)
            res = temp.test()
            time = timeit.timeit(lambda: test_cases.TestCases(to_test).test(), number = 1)

            content = []
            with open(os.path.join(app.config["FILE_UPLOADS"], filename), 'r') as f:
                for line in f:
                    content.append(line)

            os.remove(os.path.join(app.config["FILE_UPLOADS"], filename))
            return render_template('results.html', result = res, total = len(temp.answers), file = content, time = time)

        return redirect(request.url)

    return render_template('index.html', form = form)

@app.route('/results')
def results():
    return render_template('results.html', result = {}, total = 0, file = '', time = 0)

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

    print(current_user.is_admin)
    if not current_user.is_admin: return redirect('/')
    form = UploadForm()

    def is_valid(filename):
        return re.match('session_[0-9]+\.py', filename) is not None

    if request.method == "POST":
        if is_valid(form.filename.data.filename):

            filename = secure_filename(form.filename.data.filename)

            if os.path.exists(os.path.join(app.config["SESSION_UPLOADS"], filename)):
                os.remove(os.path.join(app.config["SESSION_UPLOADS"], filename))

            form.filename.data.save(os.path.join(app.config["SESSION_UPLOADS"], filename))
            return redirect('/')

        return redirect(request.url)

    return render_template('upload_session.html', form = form)

if __name__ == '__main__':
    app.run()
