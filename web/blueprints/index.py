from flask import Blueprint, render_template
from flask_login import current_user, login_required
from web.models import Course

index_template = Blueprint('index', __name__, template_folder = '../templates')

# index page shows a list of all available courses
@index_template.route('/', methods=["GET", "POST"])
@login_required
def index():
    if current_user.is_admin:
        courses = sorted(Course.query.all(), key = lambda x: x.course_num)
    else:
        courses = sorted(Course.query.filter(Course.users.any(id=current_user.id)).all(), key = lambda x: x.course_num)
    return render_template('index.html', courses = courses)