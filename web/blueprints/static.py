from flask import Blueprint, render_template
from web.utils import admin_required

import markdown
import markdown.extensions.fenced_code

static_template = Blueprint(
    'static', __name__, template_folder='../templates')

@static_template.route('/how_to/create_test_example')
@admin_required
def create_test_example():
    markdown_file = open("web/how_to/create_test_example.md", "r")
    md_template_string = markdown.markdown(
        markdown_file.read(), extensions=["fenced_code"]
    )
    return render_template('create_test_example.html', markdown=md_template_string)