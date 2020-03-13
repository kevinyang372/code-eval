from flask_login import current_user
from flask import redirect, url_for
from functools import wraps
from web import app
import os
import nbformat
from nbconvert import PythonExporter
import pygments

def read_file(file, filename):
    """Read user uploaded files"""

    file.save(os.path.join(app.config["FILE_UPLOADS"], filename))

    content = []
    with open(os.path.join(app.config["FILE_UPLOADS"], filename), 'r') as file:
        for line in file:
            content.append(line)

    os.remove(os.path.join(app.config["FILE_UPLOADS"], filename))
    return ''.join(content)


def admin_required(f):
    """Decorator for requiring admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user or not current_user.is_admin:
            return redirect(url_for('index.index'))
        return f(*args, **kwargs)
    return decorated_function


def convert_jupyter(file, filename):
    """Read jupyter notebook uploads"""

    file.save(os.path.join(app.config["FILE_UPLOADS"], filename))

    with open(os.path.join(app.config["FILE_UPLOADS"], filename)) as f:
        nb = nbformat.reads(f.read(), nbformat.NO_CONVERT)

    exporter = PythonExporter()
    source, _ = exporter.from_notebook_node(nb)

    os.remove(os.path.join(app.config["FILE_UPLOADS"], filename))
    return source


def highlight_python(code):
    """highlight python code to html"""

    formatter = pygments.formatters.HtmlFormatter(style="emacs", cssclass="codehilite")
    css_string = "<style>" + formatter.get_style_defs() + "</style>"

    return css_string + pygments.highlight(code, pygments.lexers.PythonLexer(), formatter)


def compile_results(res):
    """compile results into models"""

    compiled = {}
    for question in res:
        compiled[question] = {}

        compiled[question]['total_num'] = len(res[question])
        compiled[question]['passed_num'] = sum([1 for case in res[question] if res[question][case] == "Passed"])
        compiled[question]['reason'] = res[question]

    return compiled