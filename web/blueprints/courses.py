from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from web.models import Course, Session, Result, Case
from web.forms import CodeSumitForm, AddCourse
from web import app, db
from web.utils import read_file, admin_required
from werkzeug.utils import secure_filename
from werkzeug.datastructures import MultiDict
import timeit
import random
import string
import os

course_template = Blueprint('course', __name__, template_folder='../templates')


@course_template.route('/courses/<course_num>', methods=["GET", "POST"])
@login_required
def course(course_num):
    """Page for submitting code
    
    Required scope: User / Admin
    User could submit their code here. Submission needs to include prespecified entry
    function within the code
    """

    # check if filename is valid
    def is_valid(filename):
        if filename and '.' in filename and filename.split('.')[1] in app.config["ALLOWED_EXTENSIONS"]:
            return True
        return False

    if not current_user.is_admin and not any(int(course_num) == i.course_num for i in current_user.courses):
        flash('You have no access to this course!')
        return redirect(url_for('index'))

    form = CodeSumitForm()

    # list available sessions
    available = Session.query.filter(
        Session.course.has(course_num=course_num)).all()
    form.sessions.choices = sorted(
        [(i.session_num, 'session %s' % i.session_num) for i in available])

    if form.validate_on_submit():
        if is_valid(form.filename.data.filename):

            filename = secure_filename(form.filename.data.filename)
            to_test = read_file(form.filename.data, filename)

            # fetch session settings
            setting = Session.query.filter(Session.course.has(
                course_num=course_num)).filter_by(session_num=form.sessions.data).first()

            d = {}
            exec(setting.test_code, d)

            temp = d['TestCases'](to_test)
            res = temp.test(runtime=setting.runtime,
                            entry_point=setting.entry_point, blacklist=setting.get_blacklist())

            # record runtime
            time = timeit.timeit(lambda: d['TestCases'](to_test).test(
                runtime=setting.runtime, entry_point=setting.entry_point, blacklist=setting.get_blacklist()), number=1)

            passed_num = sum([1 for case in res if res[case] == "Passed"])

            to_add = Result(user_id=current_user.id, email=current_user.email, session_id=setting.id,
                            passed_num=passed_num, content=to_test, runtime=time, success=passed_num == len(temp.answers))
            db.session.add(to_add)

            for case in res:
                to_add.cases.append(
                    Case(case_num=case, success=res[case] == "Passed", reason=res[case]))

            db.session.commit()

            return render_template('results.html', result=res, passed=passed_num, total=len(temp.answers), file=to_test.replace(' ', '\xa0'), time=time)

        return redirect(request.url)

    return render_template('courses.html', form=form)


@course_template.route('/add_course', methods=["GET", "POST"])
@admin_required
def add_course():
    """Page for adding new courses
    
    Required scope: Admin
    User could choose to use the randomly generated registration link
    or customize their own ones
    """

    random_generated = ''.join(random.choice(
        string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(6))
    form = AddCourse(registration_link = random_generated)

    if form.validate_on_submit():

        form = AddCourse()

        if not Course.query.filter_by(course_num=form.course_num.data).first() and not Course.query.filter_by(registration=form.registration_link.data).first():
            new_course = Course(course_num=form.course_num.data,
                                registration=form.registration_link.data)
            db.session.add(new_course)
            db.session.commit()
        else:
            flash('Course num or course registration link already exists')
            return redirect(url_for('course.add_course'))

        return redirect('/')

    return render_template('add_course.html', form=form)


@course_template.route('/delete_course/<course_id>')
@admin_required
def delete_course(course_id):
    """Page for deleting courses
    
    Required scope: Admin
    Note that all sessions and results attached to that session
    will be deleted
    """

    course = Course.query.filter_by(id=course_id).first()
    if not course:
        flash('Course to delete does not exist')
        return redirect(url_for('setting.all_settings'))
    else:
        db.session.delete(course)
        db.session.commit()
        return redirect(url_for('setting.all_settings'))


@course_template.route('/change_course/<course_id>', methods=["GET", "POST"])
@admin_required
def change_course(course_id):
    """Page for changing course details
    
    Required scope: Admin
    """

    course = Course.query.filter_by(id=course_id).first()
    if not course:
        flash('Course to change does not exist')
        return redirect(url_for('setting.all_settings'))

    form = AddCourse(registration_link = course.registration, course_num = course.course_num)

    if form.validate_on_submit():

        form = AddCourse()

        if Course.query.filter_by(registration=form.registration_link.data).first():
            flash('Course with this registration link already exists')
            return redirect(url_for('course.change_course', course_id = course_id))

        course.course_num = form.course_num.data
        course.registration = form.registration_link.data

        db.session.commit()
        return redirect('/')

    return render_template('add_course.html', form=form)
