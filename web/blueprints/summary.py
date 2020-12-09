from flask import Blueprint, render_template, request
from web.models import Course, Session, Result
from web.utils import admin_required, highlight_python
from flask_breadcrumbs import default_breadcrumb_root, register_breadcrumb
from flask_login import login_required

summary_template = Blueprint(
    'summary', __name__, template_folder='../templates')

# Register the breadcrumb to be after the index page.
default_breadcrumb_root(summary_template, '.summary')


def view_course_dlc(*args, **kwargs):
    """Utility function for generating course breadcrumb."""
    course_id = request.view_args['course_id']

    # Text: the displayed text of the breadcrumb
    # Url: the link of the breadcrumb
    return [{'text': ' Course', 'url': f'/summary/{course_id}'}]


def view_session_dlc(*args, **kwargs):
    """Utility function for generating session breadcrumb."""
    course_id = request.view_args['course_id']
    session_id = request.view_args['session_id']
    return [{'text': ' Session', 'url': f'/summary/{course_id}/{session_id}'}]


def view_user_dlc(*args, **kwargs):
    """Utility function for generating user breadcrumb."""
    course_id = request.view_args['course_id']
    session_id = request.view_args['session_id']
    user_id = request.view_args['user_id']
    return [{'text': ' Student', 'url': f'/summary/{course_id}/{session_id}/{user_id}'}]


def view_result_dlc(*args, **kwargs):
    """Utility function for generating result breadcrumb."""
    course_id = request.view_args['course_id']
    session_id = request.view_args['session_id']
    user_id = request.view_args['user_id']
    result_id = request.view_args['result_id']
    return [{'text': ' Result', 'url': f'/summary/{course_id}/{session_id}/{user_id}/{result_id}'}]


@summary_template.route('/summary')
@register_breadcrumb(summary_template, '.', ' Summary')
@admin_required
def summary():
    """Summary index page."""
    courses = Course.query.all()
    return render_template('summary.html', courses=courses)


@summary_template.route('/summary/<course_id>')
@register_breadcrumb(summary_template, '.summary', '', dynamic_list_constructor=view_course_dlc)
@admin_required
def summary_session(course_id):
    """Summary page of each course."""
    sessions = Session.query.filter_by(course_id=course_id).all()
    return render_template('summary_session.html', course_id=course_id, sessions=sessions)


@summary_template.route('/summary/<course_id>/<session_id>')
@register_breadcrumb(summary_template, '.summary.course', '', dynamic_list_constructor=view_session_dlc)
@admin_required
def summary_student(course_id, session_id):
    """Summary page of each session in the course."""
    results = Result.query.filter_by(session_id=session_id).all()
    students = set([r.user for r in results])
    return render_template('summary_student.html', course_id=course_id, session_id=session_id, students=students)


@summary_template.route('/summary/<course_id>/<session_id>/<user_id>')
@register_breadcrumb(summary_template, '.summary.course.student', '', dynamic_list_constructor=view_user_dlc)
@admin_required
def summary_result(course_id, session_id, user_id):
    """Summary page of each student's submission in one session."""
    results = Result.query.filter_by(
        session_id=session_id, user_id=user_id).all()
    return render_template('summary_result.html', results=results, course_id=course_id, session_id=session_id, user_id=user_id)


@summary_template.route('/summary/<course_id>/<session_id>/<user_id>/<result_id>')
@register_breadcrumb(summary_template, '.summary.course.student.result', '', dynamic_list_constructor=view_result_dlc)
@login_required
def summary_case(course_id, session_id, user_id, result_id):
    """Individual submission details."""
    result = Result.query.filter_by(id=result_id).first()

    # Re-populate the result with saved records.
    res = {question.name: {case.case_content: case.reason for case in question.cases}
           for question in result.questions}

    # p = sorted(result.plagiarisms, key=lambda x: (-x.exact_match, -x.unifying_ast, -x.ignore_variables, -x.reordering_ast, x.edit_tree))[:3]

    return render_template('results.html', result=res, passed=result.passed_num, total=len(result.questions), file=highlight_python(result.content), time=result.runtime, i=result.id)
