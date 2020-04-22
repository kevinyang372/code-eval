from flask import Blueprint, render_template, request, redirect, url_for
from web.utils import admin_required, highlight_diff
from web.models import Result

compare_template = Blueprint('compare', __name__, template_folder='../templates')


@compare_template.route('/compare/<result_id1>/<result_id2>', methods=["GET", "POST"])
@admin_required
def compare(result_id1, result_id2):

    r1 = Result.query.filter_by(id=result_id1).first()
    r2 = Result.query.filter_by(id=result_id2).first()

    return render_template('compare.html', content=highlight_diff([r1.user.email, r2.user.email], [r1.content, r2.content]))