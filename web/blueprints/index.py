from flask import Blueprint, render_template, redirect
from flask_login import current_user, login_required
from flask_breadcrumbs import default_breadcrumb_root, register_breadcrumb
from web.models import Course
from web.forms import Register

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
