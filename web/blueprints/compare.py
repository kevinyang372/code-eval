from flask import Blueprint, render_template, request, redirect, url_for
from web.utils import admin_required
from web.models import Result

import difflib

compare_template = Blueprint('compare', __name__, template_folder='../templates')


@compare_template.route('/compare/<result_id1>/<result_id2>', methods=["GET", "POST"])
@admin_required
def compare(result_id1, result_id2):

    r1 = Result.query.filter_by(id=result_id1).first()
    r2 = Result.query.filter_by(id=result_id2).first()

    file_1 = [i + '\n' for i in r1.content.split('\n')]
    file_2 = [i + '\n' for i in r2.content.split('\n')]

    l = difflib.unified_diff(file_1, file_2, fromfile=r1.user.email, tofile=r2.user.email)
    content = []

    for line in l:
        content.append(line)

    return render_template('compare.html', content=content)