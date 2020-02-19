from flask import Blueprint, render_template
from web.models import Course, Session
from web.utils import admin_required

setting_template = Blueprint('setting', __name__, template_folder = '../templates')

@setting_template.route('/all_settings')
@admin_required
def all_settings():
    course = Course.query.all()
    return render_template('all_setting.html', course = course)

@setting_template.route('/all_settings/<course_id>')
@admin_required
def session_settings(course_id):
    session = Session.query.filter_by(course_id=course_id).all()

    total_s = len(Course.query.filter_by(id=course_id).first().users)

    for ind in range(len(session)):
        session[ind].submitted_students = len(set([t.user.id for t in session[ind].results]))

        if session[ind].submitted_students != 0:
            session[ind].passing_rate = len(set([t.user.id for t in session[ind].results if t.success ])) / float(session[ind].submitted_students)
        else:
            session[ind].passing_rate = 0

    return render_template('session_settings.html', session = session)