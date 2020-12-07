from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from web.models import Course, Session, Access
from web.forms import UploadForm
from werkzeug.utils import secure_filename
from web.utils import read_file, admin_required
from werkzeug.datastructures import MultiDict
from web import app, db

session_template = Blueprint(
    'session', __name__, template_folder='../templates')


@session_template.route('/upload_session', methods=["GET", "POST"])
@admin_required
def upload_session():
    """Page for uploading new sessions

    Required scope: Admin
    Prerequisites: Course exists
    """
    form = UploadForm()

    # Add the choice of course number dynamically
    form.course_num.choices = sorted(
        [(s.course_num, f"course {str(s.course_num)}") for s in Course.query.all()])

    if form.validate_on_submit():

        # Transform filename to a secure one
        filename = secure_filename(form.filename.data.filename)
        test_code = read_file(form.filename.data, filename)

        course_id = Course.query.filter_by(
            course_num=form.course_num.data).first().id
        to_add = {'course_id': course_id, 'runtime': form.runtime.data, 'description': form.description.data,
                  'blacklist': form.blacklist.data, 'session_num': form.session_num.data, 'test_code': test_code}

        # Update / insert session settings
        if Session.query.filter_by(course_id=course_id, session_num=form.session_num.data).first():
            s = Session.query.filter_by(
                course_id=course_id, session_num=form.session_num.data).first()
            for key, val in to_add.items():
                setattr(s, key, val)
        else:
            s = Session(**to_add)
            db.session.merge(s)

        db.session.commit()
        return redirect('/')

    return render_template('upload_session.html', form=form)


@session_template.route('/delete_session/<session_id>')
@admin_required
def delete_session(session_id):
    """Page for delete sessions

    Required scope: Admin
    Note that all results attached to the session will be deleted as well
    """
    session = Session.query.filter_by(id=session_id).first()
    if not session:
        flash('Session to delete does not exist')
        return redirect(url_for('/'))
    else:
        db.session.delete(session)
        db.session.commit()
        return redirect(url_for('setting.all_settings'))


@session_template.route('/change_session/<session_id>', methods=["GET", "POST"])
@admin_required
def change_session(session_id):
    """Page for changing session settings

    Required scope: Admin
    """
    session = Session.query.filter_by(id=session_id).first()

    if not session:
        flash('Session to change does not exist')
        return redirect(url_for('/'))

    # Populate the fields with the current settings
    form = UploadForm(
        session_num=session.session_num,
        course_num=session.course.course_num,
        description=session.description,
        runtime=session.runtime,
        blacklist=session.blacklist
    )

    form.course_num.choices = sorted(
        [(s.course_num, f"course {str(s.course_num)}") for s in Course.query.all()])

    if form.validate_on_submit():

        form = UploadForm()

        if form.filename.data:
            filename = secure_filename(form.filename.data.filename)
            test_code = read_file(form.filename.data, filename)
            session.test_code = test_code

        session.session_num = form.session_num.data
        session.description = form.description.data
        session.course.course_num = form.course_num.data
        session.runtime = form.runtime.data
        session.blacklist = form.blacklist.data

        db.session.commit()
        return redirect(url_for('setting.session_settings', course_id=session.course.id))

    return render_template('upload_session.html', form=form)


@session_template.route('/register/<link>', methods=["GET", "POST"])
@login_required
def register(link):
    """Page for registering into new courses

    Required scope: User / Admin
    This page is provided for students to register into the courses they
    are invited to. The register link for specific courses could be found
    at /all_settings
    """

    if current_user.is_admin:
        flash('You are an admin! Enjoy your privileges.')
        return redirect(url_for('index.index'))

    res = Course.query.filter_by(registration=link).first()
    if not res:
        flash('The registration link does not exist!')
        return redirect(url_for('index.index'))

    if any(user.id == current_user.id for user in res.users):
        flash('You have already registered!')
        return redirect(url_for('index.index'))

    # Create a registration access object between user and course.
    db.session.add(Access(user_id=current_user.id, course_id=res.id))
    db.session.commit()

    flash('You have successfully registered!')
    return redirect(url_for('index.index'))
