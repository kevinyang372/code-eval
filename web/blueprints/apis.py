from flask import Blueprint, request, jsonify
from web.utils import admin_required_api
from web.models import User, Result
from web import csrf

api_template = Blueprint('apis', __name__, template_folder='../templates')


@api_template.route('/check_alive', methods=["GET"])
@csrf.exempt
def check_alive():
    return jsonify(data={'message': 'It works!'})


@api_template.route('/get_score/<student_email>/<session_id>', methods=["POST"])
@admin_required_api
@csrf.exempt
def get_score(student_email, session_id):
    user = User.query.filter_by(email=student_email).first()
    if not user: return jsonify(data={'message': 'Fails to find user email'})
    results = Result.query.filter_by(user_id = user.id, session_id=session_id).all()
    return jsonify(data={'result': str(list(i.passed_num for i in results))})