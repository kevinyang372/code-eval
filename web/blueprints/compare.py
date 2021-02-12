from flask import Blueprint, render_template, request, redirect, url_for
from web.utils import admin_required
from web.plagiarism import Plagiarism
from web.models import Result, Session

compare_template = Blueprint(
    'compare', __name__, template_folder='../templates')


@compare_template.route('/compare/<result_id1>/<result_id2>')
@admin_required
def compare(result_id1, result_id2):
    """Endpoint for comparing two user submissions."""

    p = Plagiarism(result_id1, result_id2)

    # Get the similarity level and highlighted code block.

    parsed1, parsed2 = p.highlight_diff()
    similarity = p.tree_distance()

    # Compile a list of test results using different plagiarism detection algorithms.
    comparison = p.compile_plagarism_report_two()

    return render_template('compare.html', email1=p.result_1.email, email2=p.result_2.email, parsed1=parsed1, parsed2=parsed2, comparison=comparison, similarity=similarity)


@compare_template.route('/compare/<result_id1>', methods=['GET', 'POST'])
@admin_required
def compare_index(result_id1):
    """Endpoint for showing a list of results in comparison with the current submission."""

    r1 = Result.query.filter_by(id=result_id1).first()

    # Filter out results that are created by the same user.
    rs = [r for r in Result.query.filter_by(session_id=r1.session_id).all() if r.user_id != r1.user_id]

    results = []
    similarities = []

    for result in rs:
        p = Plagiarism(r1, result.id)
        results.append((p.tree_distance(), result))

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
                p = Plagiarism(r1.id, r2.id)
                report = p.compile_plagarism_report_two()

                c.append({
                    'similarity': round(p.tree_distance(), 3),
                    'exact_match': report[0],
                    'unifying_ast_match': report[1],
                    'ast_match_ignoring_variables': report[2],
                    'comment_edit_distance': round(report[3], 3),
                    'r1': r1.id,
                    'r2': r2.id,
                    'email1': r1.user.email,
                    'email2': r2.user.email
                })

        return c

    all_submitted_users = list(Session.query.filter_by(id=session_id).first().get_passed_submission_students())
    list_of_results = Result.query.filter_by(session_id=session_id, success=True).all()
    res = {}

    # Query against all submitted users.
    for u1 in range(len(all_submitted_users)):
        user_1 = all_submitted_users[u1]
        result_user_1 = max(filter(lambda x: x.user_id == user_1.id, list_of_results), key=lambda x: x.id)
        temp = []

        for u2 in range(len(all_submitted_users)):
            if u1 == u2:
                continue
            user_2 = all_submitted_users[u2]
            result_user_2 = max(filter(lambda x: x.user_id == user_2.id, list_of_results), key=lambda x: x.id)

            temp.extend(compare_two_users([result_user_1], [result_user_2]))

        # Sort reversely based on similarity.
        temp.sort(key=lambda x: x['similarity'], reverse=True)
        res[result_user_1.email] = temp

    return render_template('plagiarism_session.html', results=res)
