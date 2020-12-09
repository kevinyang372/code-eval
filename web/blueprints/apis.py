from flask import Blueprint, request, jsonify, make_response
from web.utils import admin_required_api, user_required_api, is_valid, read_file, convert_jupyter, compile_results
from werkzeug.utils import secure_filename
from web.models import User, Result, Session, Question, Case
from web import csrf, db
import pybadges
import timeit

api_template = Blueprint('apis', __name__, template_folder='../templates')


@api_template.route('/check_alive', methods=["GET"])
@csrf.exempt
def check_alive():
    """Check if the api endpoint is alive."""
    return jsonify(data={'message': 'It works!'})


@api_template.route('/get_score/<student_email>/<session_id>', methods=["POST"])
@admin_required_api
@csrf.exempt
def get_score(student_email, session_id):
    """Get a list of scores for all user submission to a specific session."""
    user = User.query.filter_by(email=student_email).first()
    if not user:
        return jsonify(data={'message': 'Fails to find user email'})
    results = Result.query.filter_by(
        user_id=user.id, session_id=session_id).all()
    return jsonify(data={'result': str(list(i.passed_num for i in results))})


@api_template.route('/submit/<session_id>', methods=["POST"])
@user_required_api
@csrf.exempt
def submit(session_id):
    """Endpoint functioning similarly to the submission page."""
    if 'file' not in request.files:
        return jsonify(data={'message': 'No file part'})

    file = request.files['file']
    user = User.query.filter_by(email=request.form['email']).first()
    setting = Session.query.filter_by(id=session_id).first()

    if not setting:
        return jsonify(data={'message': 'Session not found'})

    if file and is_valid(file.filename):
        filename = secure_filename(file.filename)

        if filename.split('.')[1] == 'py':
            to_test = read_file(file, filename)
        else:
            to_test = convert_jupyter(file, filename)

        d = {}
        exec(setting.test_code, d)

        temp = d['TestCases'](to_test)
        res = temp.test(runtime=setting.runtime,
                        blacklist=setting.get_blacklist())

        # Record runtime.
        time = round(timeit.timeit(lambda: d['TestCases'](to_test).test(
            runtime=setting.runtime, blacklist=setting.get_blacklist()), number=1), 3)

        compiled = compile_results(res)
        passed_num = sum([1 for question in compiled if compiled[question]
                          ['passed_num'] == compiled[question]['total_num']])

        to_add = Result(user_id=user.id, email=user.email, session_id=setting.id,
                        passed_num=passed_num, content=to_test, runtime=time, success=passed_num == len(temp.answers))
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

        return jsonify(data={'message': compiled})


@api_template.route('/badges')
def serve_badge():
    """Serve a badge image based on the request query string."""
    badge = pybadges.badge(left_text=request.args.get('left_text'),
                           right_text=request.args.get('right_text'),
                           left_color=request.args.get('left_color'),
                           right_color=request.args.get('right_color'),
                           logo=request.args.get('logo'))

    response = make_response(badge)
    response.content_type = 'image/svg+xml'
    return response
