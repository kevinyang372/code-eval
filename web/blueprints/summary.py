from flask import Blueprint, render_template
from web.models import Course, Session, Result
from web.utils import admin_required, highlight_python

summary_template = Blueprint(
    'summary', __name__, template_folder='../templates')


@summary_template.route('/summary')
@admin_required
def summary():
    """Summary index page"""
    courses = Course.query.all()
    return render_template('summary.html', courses=courses)


@summary_template.route('/summary/<course_id>')
@admin_required
def summary_session(course_id):
    """Summary page of each course"""
    sessions = Session.query.filter_by(course_id=course_id).all()
    return render_template('summary_session.html', course_id=course_id, sessions=sessions)


@summary_template.route('/summary/<course_id>/<session_id>')
@admin_required
def summary_student(course_id, session_id):
    """Summary page of each session in the course"""
    results = Result.query.filter_by(session_id=session_id).all()
    students = set([r.user for r in results])
    return render_template('summary_student.html', course_id=course_id, session_id=session_id, students=students)


@summary_template.route('/summary/<course_id>/<session_id>/<user_id>')
@admin_required
def summary_result(course_id, session_id, user_id):
    """Summary page of each student's submission in one session"""
    results = Result.query.filter_by(
        session_id=session_id, user_id=user_id).all()
    return render_template('summary_result.html', results=results, course_id=course_id, session_id=session_id, user_id=user_id)


@summary_template.route('/result/<result_id>')
@admin_required
def summary_case(result_id):
    """Individual submission details"""
    result = Result.query.filter_by(id=result_id).first()
    res = {question.name: {case.case_num: case.reason for case in question.cases} for question in result.questions}

    p = sorted(result.plagiarisms, key=lambda x: (-x.exact_match, -x.unifying_ast, -x.ignore_variables, -x.reordering_ast, x.edit_tree))[:3]
    
    return render_template('results.html', result=res, passed=result.passed_num, total=len(result.questions), file=highlight_python(result.content), time=result.runtime, plagiarism=p, i = result.id)
