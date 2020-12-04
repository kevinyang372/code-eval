from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from web.models import Course
from web.forms import AddCourse
from web import app, db
from web.utils import admin_required
import random
import string

course_template = Blueprint('course', __name__, template_folder='../templates')


@course_template.route('/add_course', methods=["GET", "POST"])
@admin_required
def add_course():
    """Page for adding new courses

    Required scope: Admin
    User could choose to use the randomly generated registration link
    or customize their own ones
    """

    # Randomly generate a default registration link.
    random_generated = ''.join(random.choice(
        string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(6))
    form = AddCourse(registration_link=random_generated)

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

    # Populate the form with existing records.
    form = AddCourse(registration_link=course.registration,
                     course_num=course.course_num)

    if form.validate_on_submit():

        form = AddCourse()

        if Course.query.filter_by(registration=form.registration_link.data).first():
            flash('Course with this registration link already exists')
            return redirect(url_for('course.change_course', course_id=course_id))

        course.course_num = form.course_num.data
        course.registration = form.registration_link.data

        db.session.commit()
        return redirect('/')

    return render_template('add_course.html', form=form)
