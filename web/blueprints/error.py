from flask import Blueprint, render_template

error_template = Blueprint('error', __name__, template_folder='../templates')


@error_template.app_errorhandler(404)
def handle_404(err):
    """Template for returning 404 error page."""
    return render_template('error.html', error='404'), 404


@error_template.app_errorhandler(500)
def handle_500(err):
    """Template for returning 500 error page."""
    return render_template('error.html', error='404'), 500
