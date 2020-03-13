from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from web.models import Session, Result, Question, Case
from werkzeug.utils import secure_filename
from web.forms import CodeSumitForm
from web.utils import read_file, convert_jupyter, highlight_python, compile_results
from web import app, db
import timeit

submission_template = Blueprint('submission', __name__, template_folder='../templates')


@submission_template.route('/submit/<course_id>', methods=["GET", "POST"])
@login_required
def submission_index(course_id):
    """Index page for submitting code
    
    Required scope: User / Admin
    Index page for showing all available sessions user can submit to.
    """
    available = Session.query.filter_by(course_id=course_id).all()
    return render_template('submission_index.html', sessions = available, course_id = course_id)
    

@submission_template.route('/submit/<course_id>/<session_id>', methods=["GET", "POST"])
@login_required
def submission(course_id, session_id):
    """Page for submitting code
    
    Required scope: User / Admin
    User could submit their code here. Submission needs to include prespecified entry
    function within the code
    """

    # check if filename is valid
    def is_valid(filename):
        if filename and '.' in filename and filename.split('.')[1] in app.config["ALLOWED_EXTENSIONS"]:
            return True
        return False

    if not current_user.is_admin and not any(int(course_id) == i.id for i in current_user.courses):
        flash('You have no access to this course!')
        return redirect(url_for('index.index'))

    setting = Session.query.filter_by(id=session_id).first()
    form = CodeSumitForm()

    if form.validate_on_submit():
        if (form.filename.data and is_valid(form.filename.data.filename)) or form.text.data:

            if form.filename.data and is_valid(form.filename.data.filename):
                filename = secure_filename(form.filename.data.filename)

                if filename.split('.')[1] == 'py':
                    to_test = read_file(form.filename.data, filename)
                else:
                    to_test = convert_jupyter(form.filename.data, filename)
            else:
                to_test = form.text.data

            d = {}
            exec(setting.test_code, d)

            temp = d['TestCases'](to_test)
            res = temp.test(runtime=setting.runtime, blacklist=setting.get_blacklist())

            # record runtime
            time = timeit.timeit(lambda: d['TestCases'](to_test).test(
                runtime=setting.runtime, blacklist=setting.get_blacklist()), number=1)

            compiled = compile_results(res)
            passed_num = sum([1 for question in compiled if compiled[question]['passed_num'] == compiled[question]['total_num']])

            to_add = Result(user_id=current_user.id, email=current_user.email, session_id=setting.id,
                            passed_num=passed_num, content=to_test, runtime=time, success=passed_num == len(temp.answers))
            db.session.add(to_add)

            for question in compiled:
                q = Question(passed_num=compiled[question]['passed_num'], name=question)
                for reason in compiled[question]['reason']:
                    r = compiled[question]['reason'][reason]
                    q.cases.append(Case(case_num=reason, success=r == "Passed", reason=r))
                to_add.questions.append(q)

            db.session.commit()

            # return render_template('results.html', result=res, passed=passed_num, total=len(temp.answers), file=to_test.replace(' ', '\xa0'), time=time)
            return render_template('results.html', result=res, passed=passed_num, total=len(temp.answers), file=highlight_python(to_test), time=time)

        return redirect(request.url)

    return render_template('submissions.html', form=form, session=setting)