from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required
from flask_breadcrumbs import default_breadcrumb_root, register_breadcrumb
from web.models import Session, Result, Question, Case, Codecacher, Course, Plagiarism
from werkzeug.utils import secure_filename
from web.forms import CodeSumitForm
from web.utils import is_valid, read_file, convert_jupyter, highlight_python_with_flake8, compile_results, flake8_test, flake8_parser
from web import app, db, csrf
from time import gmtime, strftime
import timeit

submission_template = Blueprint(
    'submission', __name__, template_folder='../templates')

# Register the breadcrumb to be after the index page.
default_breadcrumb_root(submission_template, '.index')


def view_course_dlc(*args, **kwargs):
    """Utility function for generating course breadcrumb."""
    course_id = request.view_args['course_id']
    course_num = Course.query.filter_by(id=course_id).first().course_num

    # Text: the displayed text of the breadcrumb
    # Url: the link of the breadcrumb
    return [{'text': f" Course {course_num}", 'url': f'/submit/{course_id}'}]


def view_session_dlc(*args, **kwargs):
    """Utility function for generating session breadcrumb."""
    course_id = request.view_args['course_id']
    session_id = request.view_args['session_id']

    session_num = Session.query.filter_by(id=session_id).first().session_num
    return [{'text': f" Session {session_num}", 'url': f'/submit/{course_id}/{session_id}'}]


@submission_template.route('/submit/<course_id>', methods=["GET", "POST"])
@register_breadcrumb(submission_template, '.', '', dynamic_list_constructor=view_course_dlc)
@login_required
def submission_index(course_id):
    """Index page for submitting code.

    Required scope: User / Admin
    Index page for showing all available sessions user can submit to.
    """
    available = Session.query.filter_by(course_id=course_id).all()
    course = Course.query.filter_by(id=course_id).first()
    return render_template('submission_index.html', sessions=available, course=course)


@submission_template.route('/submit/<course_id>/<session_id>', methods=["GET", "POST"])
@register_breadcrumb(submission_template, '.course', '', dynamic_list_constructor=view_session_dlc)
@login_required
def submission(course_id, session_id):
    """Page for submitting code.

    Required scope: User / Admin
    User could submit their code here. Submission needs to include prespecified entry
    function within the code
    """

    # Check if current user has access to this session
    if not current_user.is_admin and not any(int(course_id) == i.id for i in current_user.courses):
        flash('You have no access to this course!')
        return redirect(url_for('index.index'))

    cache = Codecacher.query.filter_by(
        user_id=current_user.id, session_id=session_id).first()
    setting = Session.query.filter_by(id=session_id).first()

    # Fill the code field.
    if cache:
        pre_filled = cache.text
    else:
        d = {}
        exec(setting.test_code, d)

        pre_filled = ""
        dummy = d['TestCases']('DUMMY')

        for function_name in dummy.parameters:
            pre_filled += f"def {function_name}(*args):\n\tpass\n\n\n"

    form = CodeSumitForm(
        text=pre_filled
    )

    if form.validate_on_submit():
        # Check if user submission contains code to test on.
        if (form.filename.data and is_valid(form.filename.data.filename)) or form.text.data:

            if form.filename.data and is_valid(form.filename.data.filename):
                filename = secure_filename(form.filename.data.filename)

                if filename.split('.')[1] == 'py':
                    to_test = read_file(form.filename.data, filename)
                else:
                    to_test = convert_jupyter(form.filename.data, filename)  # Convert jupyter notebook to python

                style_check = flake8_test(to_test, filename)
            else:
                to_test = form.text.data
                style_check = flake8_test(to_test, "user_submission.py")

            d = {}
            exec(setting.test_code, d)  # Compile the test code

            # Read the user submitted code
            temp = d['TestCases'](to_test)

            res = temp.test(runtime=setting.runtime,
                            blacklist=setting.get_blacklist())

            # Record runtime
            time = round(timeit.timeit(lambda: d['TestCases'](to_test).test(
                runtime=setting.runtime, blacklist=setting.get_blacklist()), number=1), 3)

            # Convert the test result to correct formatting
            compiled = compile_results(res)
            passed_num = sum([1 for question in compiled if compiled[question]
                              ['passed_num'] == compiled[question]['total_num']])

            ts = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            to_add = Result(
                user_id=current_user.id,
                email=current_user.email,
                session_id=setting.id,
                passed_num=passed_num,
                content=to_test,
                runtime=time,
                success=passed_num == len(temp.answers),
                ts=ts,
                style_check=style_check
            )

            db.session.add(to_add)

            for question in compiled:
                q = Question(
                    passed_num=compiled[question]['passed_num'], name=question)
                for reason in compiled[question]['reason']:
                    r = compiled[question]['reason'][reason]
                    q.cases.append(
                        Case(case_content=reason, success=r == "Passed", reason=r))
                to_add.questions.append(q)

            db.session.commit()

            return render_template(
                'results.html', 
                result=res,
                passed=passed_num,
                total=len(temp.answers),
                file=highlight_python_with_flake8(to_test, flake8_parser(style_check)),
                time=time,
                i=id
            )

        return redirect(request.url)

    return render_template('submissions.html', form=form, session=setting)


@submission_template.route('/codecacher/<session_id>', methods=["POST"])
@login_required
@csrf.exempt
def codecacher(session_id):
    """Page for caching student code submissions

    Everytime user made an input in the code submission form, the changes will be saved into the database here
    """

    text = request.json['data']

    codecacher = Codecacher.query.filter_by(
        user_id=current_user.id, session_id=int(session_id)).first()

    # Update if code cache exists. Otherwise create a new code cache object.
    if codecacher:
        codecacher.text = text
    else:
        codecacher = Codecacher(user_id=current_user.id,
                                session_id=int(session_id), text=text)
        db.session.add(codecacher)
    db.session.commit()
    return jsonify(data={'message': 'Successfully cached content'})
