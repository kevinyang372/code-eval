from flask import Blueprint, render_template, request, redirect, url_for
from web.utils import admin_required, highlight_diff, highlight_diff_temp
from web.models import Result

compare_template = Blueprint('compare', __name__, template_folder='../templates')


@compare_template.route('/compare/<result_id1>/<result_id2>')
@admin_required
def compare(result_id1, result_id2):

    r1 = Result.query.filter_by(id=result_id1).first()
    r2 = Result.query.filter_by(id=result_id2).first()

    parsed1, parsed2 = highlight_diff_temp([r1.content, r2.content])

    return render_template('compare.html', parsed1 = parsed1, parsed2 = parsed2)


@compare_template.route('/compare/<result_id1>')
@admin_required
def compare_index(result_id1):

    r1 = Result.query.filter_by(id=result_id1).first()
    results = Result.query.filter_by(session_id = r1.session_id)

    return render_template('compare_index.html', results = results, r1 = r1.id)