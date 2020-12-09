from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from flask_breadcrumbs import default_breadcrumb_root, register_breadcrumb
from web.models import Course, Result
from web.utils import convert_timedelta_to_string
from web.forms import Register
from datetime import datetime
import pybadges

index_template = Blueprint('index', __name__, template_folder='../templates')
default_breadcrumb_root(index_template, '.')


@index_template.route('/', methods=["GET", "POST"])
@register_breadcrumb(index_template, '.', 'Home')
@login_required
def index():
    """Page for the list of courses available to the user

    Required scope: User / Admin
    This page only displays courses that the user has access to
    """
    form = Register()

    if current_user.is_admin:
        # If user is an admin, give all the course lists.
        courses = sorted(Course.query.all(), key=lambda x: x.course_num)
    else:
        courses = sorted(Course.query.filter(Course.users.any(
            id=current_user.id)).all(), key=lambda x: x.course_num)

    if form.validate_on_submit():
        register_link = form.registration_link.data
        return redirect(f'/register/{register_link}')

    return render_template('index.html', courses=courses, form=form)


@index_template.route('/my_submissions')
@register_breadcrumb(index_template, '.home', ' My Submission')
@login_required
def my_submissions():
    """Page for viewing a list of past submissions."""

    results = Result.query.filter_by(user_id=current_user.id).all()
    current_time = datetime.utcnow()

    results.sort(key=lambda x: x.get_timedelta())

    for r in results:
        r.badge = url_for('apis.serve_badge', **{
            'left_text': convert_timedelta_to_string(r.get_timedelta()),
            'right_text': 'Passed' if r.success else 'Failed',
            'left_color': '#555',
            'right_color': '#008000' if r.success else '#800000'
        })

    return render_template('my_submissions.html', results=results)
