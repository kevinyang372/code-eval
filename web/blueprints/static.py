from flask import Blueprint, render_template
from flask_login import login_required
from web.utils import admin_required

import markdown
import markdown.extensions.fenced_code

static_template = Blueprint(
    'static', __name__, template_folder='../templates')


@static_template.route('/how_to/create_test_example')
@admin_required
def create_test_example():
    """How to page on creating test examples."""

    # Read markdown file from folder.
    markdown_file = open("web/how_to/create_test_example.md", "r")
    md_template_string = markdown.markdown(
        markdown_file.read(), extensions=["fenced_code"]
    )
    return render_template('markdown.html', markdown=md_template_string)


@static_template.route('/how_to/code_submission')
@login_required
def code_submission():
    """How to page on submitting code."""

    # Read markdown file from folder.
    markdown_file = open("web/how_to/code_submission.md", "r")
    md_template_string = markdown.markdown(
        markdown_file.read(), extensions=["fenced_code"]
    )
    return render_template('markdown.html', markdown=md_template_string)


@static_template.route('/about')
@login_required
def about():
    """How to page on submitting code."""

    # Read markdown file from folder.
    markdown_file = open("web/how_to/about.md", "r")
    md_template_string = markdown.markdown(
        markdown_file.read(), extensions=["fenced_code"]
    )
    return render_template('markdown.html', markdown=md_template_string)
