from flask import Blueprint, render_template, request, redirect, url_for
from web.utils import admin_required, highlight_diff, highlight_diff_temp, compile_plagarism_report_two
from web.models import Result, Session
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
    rs = [r for r in Result.query.filter_by(session_id=r1.session_id).all() if r.user_id != r1.user_id]

    results = []
    similarities = []

    for result in rs:
        _, _, similarity = highlight_diff_temp([r1.content, result.content])
        results.append((similarity, result))

    form = FilterResult()
    return render_template('compare_index.html', form=form, results=results, r1=r1.id)

@compare_template.route('/plagiarism/<session_id>', methods=['GET', 'POST'])
@admin_required
def plagiarism_session(session_id):
    """Endpoint for showing all the plagiarism comparisons in a specific session."""

    def compare_two_users(results_1, results_2):
        """Utility function for comparing plagiarim results between two users."""

        c = []
        for r1 in results_1:
            for r2 in results_2:
                _, _, similarity = highlight_diff_temp([r1.content, r2.content])
                c.append((similarity, r1.id, r2.id, r1.user.email, r2.user.email))

        return c

    all_submitted_users = list(Session.query.filter_by(id=session_id).first().get_passed_submission_students())
    list_of_results = Result.query.filter_by(session_id=session_id, success=True).all()
    res = []

    # Query against all submitted users.
    for u1 in range(len(all_submitted_users) - 1):
        user_1 = all_submitted_users[u1]
        result_user_1 = list(filter(lambda x: x.user_id == user_1.id, list_of_results)) # Filter out the results submitted by user_1

        for u2 in range(u1 + 1, len(all_submitted_users)):
            user_2 = all_submitted_users[u2]
            result_user_2 = list(filter(lambda x: x.user_id == user_2.id, list_of_results)) # Filter out the results submitted by user_2

            res.extend(compare_two_users(result_user_1, result_user_2))

    # Sort reversely based on similarity.
    res.sort(reverse=True)
    form = FilterResult()

    return render_template('plagiarism_session.html', results=res, form=form)




