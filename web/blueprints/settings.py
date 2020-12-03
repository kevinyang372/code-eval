from flask import Blueprint, render_template
from web.models import Course, Session
from web.utils import admin_required

setting_template = Blueprint(
    'setting', __name__, template_folder='../templates')


@setting_template.route('/all_settings')
@admin_required
def all_settings():
    """Setting index page

    Required scope: Admin
    """
    course = Course.query.all()
    return render_template('all_setting.html', course=course)


@setting_template.route('/all_settings/<course_id>')
@admin_required
def session_settings(course_id):
    """Setting page for each session

    Required scope: Admin
    """
    session = Session.query.filter_by(course_id=course_id).all()
    return render_template('session_settings.html', session=session)
