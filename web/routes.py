from flask import render_template, request, redirect, url_for, flash
from web import app, db
from web.forms import CodeSumitForm, LoginForm, UploadForm, AddSeminar
from web.models import User, Result, Case, Seminar, Session, Access
from werkzeug.utils import secure_filename
from flask_login import current_user, login_user, login_required, logout_user
from datetime import datetime
from werkzeug.datastructures import MultiDict
import timeit
import os
import importlib
import random
import string
import shutil

import sys
sys.path.append('web')

def read_file(file, filename):
    file.save(os.path.join(app.config["FILE_UPLOADS"], filename))

    content = []
    with open(os.path.join(app.config["FILE_UPLOADS"], filename), 'r') as file:
        for line in file:
            content.append(line)
    
    os.remove(os.path.join(app.config["FILE_UPLOADS"], filename))
    return ''.join(content)


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
            to_test = read_file(form.filename.data, filename)

            # fetch session settings
            setting = Session.query.filter(Session.seminar.has(seminar_num=seminar_num)).filter_by(session_num=form.sessions.data).first()

            d = {}
            exec(setting.test_code, d)

            temp = d['TestCases'](to_test)
            res = temp.test(runtime = setting.runtime, entry_point = setting.entry_point, blacklist = setting.get_blacklist())

            # record runtime
            time = timeit.timeit(lambda: d['TestCases'](to_test).test(runtime = setting.runtime, entry_point = setting.entry_point, blacklist = setting.get_blacklist()), number = 1)

            passed_num = sum([1 for case in res if res[case] == "Passed"])

            to_add = Result(user_id = current_user.id, email = current_user.email, session_id = setting.id, passed_num = passed_num, content = to_test, runtime = time, success = passed_num == len(temp.answers))
            db.session.add(to_add)

            for case in res:
                to_add.cases.append(Case(case_num = case, success = res[case] == "Passed", reason = res[case]))

            db.session.commit()

            return render_template('results.html', result = res, passed = passed_num, total = len(temp.answers), file = to_test.replace(' ', '\xa0'), time = time)

        return redirect(request.url)

    return render_template('seminars.html', form = form)

@app.route('/summary')
@login_required
def summary():
    if not current_user.is_admin: return redirect('/')
    seminars = Seminar.query.all()
    return render_template('summary.html', seminars = seminars)

@app.route('/summary/<seminar_id>')
@login_required
def summary_session(seminar_id):
    if not current_user.is_admin: return redirect('/')
    sessions = Session.query.filter_by(seminar_id=seminar_id).all()
    return render_template('summary_session.html', seminar_id = seminar_id, sessions = sessions)

@app.route('/summary/<seminar_id>/<session_id>')
@login_required
def summary_student(seminar_id, session_id):
    if not current_user.is_admin: return redirect('/')
    results = Result.query.filter_by(session_id=session_id).all()
    students = set([r.user for r in results])
    return render_template('summary_student.html', seminar_id = seminar_id, session_id = session_id, students = students)

@app.route('/summary/<seminar_id>/<session_id>/<user_id>')
@login_required
def summary_result(seminar_id, session_id, user_id):
    if not current_user.is_admin: return redirect('/')
    results = Result.query.filter_by(session_id=session_id, user_id=user_id).all()
    return render_template('summary_result.html', results = results, seminar_id = seminar_id, session_id = session_id, user_id = user_id)

@app.route('/summary/<seminar_id>/<session_id>/<user_id>/<result_id>')
@login_required
def summary_case(seminar_id, session_id, user_id, result_id):
    if not current_user.is_admin: return redirect('/')
    result = Result.query.filter_by(id = result_id).first()
    res = {case.case_num:case.reason for case in result.cases}

    return render_template('results.html', result = res, passed = result.passed_num, total = len(result.cases), file = result.content.replace(' ', '\xa0'), time = result.runtime)

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
        test_code = read_file(form.filename.data, filename)

        seminar_id = Seminar.query.filter_by(seminar_num=form.seminar_num.data).first().id
        to_add = {'seminar_id': seminar_id, 'entry_point': form.entry_point.data, 'runtime': form.runtime.data, 'blacklist': form.blacklist.data, 'session_num': form.session_num.data, 'test_code': test_code}

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
            return redirect(url_for('change_course'))

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
        db.session.delete(session)
        db.session.commit()
        return redirect(url_for('all_settings'))

@app.route('/change_course/<seminar_id>', methods=["GET", "POST"])
@login_required
def change_course(seminar_id):
    if not current_user.is_admin: return redirect('/')

    seminar = Seminar.query.filter_by(id=seminar_id).first()
    if not seminar:
        flash('Course to change does not exist')
        return redirect(url_for('all_settings'))
    
    form = AddSeminar(formdata=MultiDict({'registration_link': seminar.registration, 'seminar_num': seminar.seminar_num}))

    if request.method == "POST":

        form = AddSeminar()

        seminar.seminar_num = form.seminar_num.data
        seminar.registration = form.registration_link.data

        db.session.commit()
        return redirect('/')

    return render_template('add_seminar.html', form = form)
