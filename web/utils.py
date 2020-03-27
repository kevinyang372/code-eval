from flask_login import current_user
from flask import redirect, url_for, flash, request, jsonify
from functools import wraps
from web import app
import os
import nbformat
from nbconvert import PythonExporter
import pygments
from web.models import User
import json


def is_valid(filename):
    """Validate user uploaded files' filename"""
    if filename and '.' in filename and filename.split('.')[1] in app.config["ALLOWED_EXTENSIONS"]:
        return True
    return False


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
            flash('You have no access to this page')
            return redirect(url_for('index.index'))
        return f(*args, **kwargs)
    return decorated_function


def user_required_api(f):
    """Decorator for requiring user access in api"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if request.json:
            email = str(request.json['credentials']['email'])
            password = str(request.json['credentials']['password'])
        elif request.form:
            email = str(request.form['email'])
            password = str(request.form['password'])

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            return jsonify(data={'message': 'Fails to verify user credentials'})
        return f(*args, **kwargs)
    return decorated_function


def admin_required_api(f):
    """Decorator for requiring admin access in api"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        email = str(request.json['credentials']['email'])
        password = str(request.json['credentials']['password'])

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password) or not user.is_admin:
            return jsonify(data={'message': 'Fails to verify user credentials'})
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