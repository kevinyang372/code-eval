from flask import Blueprint, render_template, request, redirect, url_for
from web.utils import admin_required, highlight_diff, highlight_diff_temp, compile_plagarism_report_two
from web.models import Result
from web.forms import FilterResult

compare_template = Blueprint(
    'compare', __name__, template_folder='../templates')


@compare_template.route('/compare/<result_id1>/<result_id2>')
@admin_required
def compare(result_id1, result_id2):

    r1 = Result.query.filter_by(id=result_id1).first()
    r2 = Result.query.filter_by(id=result_id2).first()

    parsed1, parsed2, similiarity = highlight_diff_temp(
        [r1.content, r2.content])
    comparison = compile_plagarism_report_two([r1.content, r2.content])

    return render_template('compare.html', email1=r1.email, email2=r2.email, parsed1=parsed1, parsed2=parsed2, comparison=comparison, similiarity=similiarity)


@compare_template.route('/compare/<result_id1>', methods=['GET', 'POST'])
@admin_required
def compare_index(result_id1):

    r1 = Result.query.filter_by(id=result_id1).first()
    results = Result.query.filter_by(session_id=r1.session_id)
    form = FilterResult()

    if form.validate_on_submit():

        res = []
        for result in results:
            _, _, similiarity = highlight_diff_temp(
                [r1.content, result.content])
            if similiarity > form.threshold.data:
                res.append(result)

        return render_template('compare_index.html', form=form, results=res, r1=r1.id)

    return render_template('compare_index.html', form=form, results=results, r1=r1.id)
