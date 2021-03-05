from flask_login import current_user
from flask import redirect, url_for, flash, request, jsonify

import os
import re
import collections
import nbformat
import requests
import pygments
import json
from functools import wraps
from nbconvert import PythonExporter
from subprocess import check_output, STDOUT, CalledProcessError

from web import app
from web.models import User, Result


def get_google_provider_cfg():
    """Utility function for logging in google."""
    return requests.get("https://accounts.google.com/.well-known/openid-configuration").json()


def is_valid(filename):
    """Validate user uploaded files' filename."""
    if filename and '.' in filename and filename.split('.')[1] in app.config["ALLOWED_EXTENSIONS"]:
        return True
    return False


def convert_timedelta_to_string(timed):
    """Convert timedelta to string of 'x amount of time ago'."""
    if timed.days > 0:
        return f"{timed.days} days ago" if timed.days > 1 else f"{timed.days} day ago"
    elif timed.seconds // 3600 > 0:
        return f"{timed.seconds // 3600} hours ago" if timed.seconds // 3600 > 1 else f"{timed.seconds // 3600} hour ago"
    elif timed.seconds // 60 > 0:
        return f"{timed.seconds // 60} minutes ago" if timed.seconds // 60 > 1 else f"{timed.seconds // 60} minute ago"
    else:
        return "Just now"


def flake8_test(to_test, filename):
    """Python flake8 style test."""
    if filename.split(".")[1] == "ipynb":
        filename = filename.split(".")[0] + ".py"

    path = os.path.join(app.config["FILE_UPLOADS"], filename)
    with open(path, 'w') as file:
        file.write(to_test)

    style_check = "Passed Python Style Check."
    rules_to_ignore = ["W191"]

    try:
        check_output(
            ["flake8", f"--ignore={','.join(rules_to_ignore)}", path], stderr=STDOUT)
    except CalledProcessError as e:
        style_check = e.output.decode("utf-8")
    except Exception as e:
        style_check = f"Failed to load flake8 module {e}"

    os.remove(path)
    return style_check


def flake8_parser(flake8_output):
    """Parse the flake8 output.

    Default formatting: '%(path)s:%(row)d:%(col)d: %(code)s %(text)s'.
    """
    warnings = flake8_output.split("\n")
    matching_rules = "(\S+):(\d+):(\d+): (\S+) (.+)"

    results = []
    for warning in warnings:
        matched = re.match(matching_rules, warning)

        try:
            if matched:
                line_num = matched.group(2)
                word_num = matched.group(3)
                rule_code = matched.group(4)
                warn_text = matched.group(5)

                results.append((line_num, word_num, rule_code, warn_text))
        except Exception as e:
            print(e)
            continue

    return results


def read_file(file, filename):
    """Read user uploaded files."""

    file.save(os.path.join(app.config["FILE_UPLOADS"], filename))

    content = []
    with open(os.path.join(app.config["FILE_UPLOADS"], filename), 'r') as file:
        for line in file:
            content.append(line)

    os.remove(os.path.join(app.config["FILE_UPLOADS"], filename))

    return ''.join(content)


def admin_required(f):
    """Decorator for requiring admin access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user or not current_user.is_admin:
            flash('You have no access to this page')
            return redirect(url_for('index.index'))
        return f(*args, **kwargs)
    return decorated_function


def user_required_api(f):
    """Decorator for requiring user access in api."""
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
    """Decorator for requiring admin access in api."""
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
    """Read jupyter notebook uploads."""

    # Save the uploaded jupyter notebook into a temporary folder.
    file.save(os.path.join(app.config["FILE_UPLOADS"], filename))

    # Read in jupyter notebooks as plain text.
    with open(os.path.join(app.config["FILE_UPLOADS"], filename)) as f:
        nb = nbformat.reads(f.read(), nbformat.NO_CONVERT)

    # Use exporter to convert jupyter notebook to Python.
    exporter = PythonExporter()
    source, _ = exporter.from_notebook_node(nb)

    # Remove the temporary file.
    os.remove(os.path.join(app.config["FILE_UPLOADS"], filename))
    return source


def highlight_python(code):
    """Highlight python code to html."""

    code = code.replace('\t', '    ')
    formatter = pygments.formatters.HtmlFormatter(
        style="emacs", cssclass="codehilite")
    css_string = "<style>" + formatter.get_style_defs() + "</style>"

    for line in code.split('\n'):
        css_string += pygments.highlight(line,
                                         pygments.lexers.PythonLexer(), formatter)
    return css_string


def highlight_python_with_flake8(code, err):
    """Highlight python code with flake8 errors."""

    errors = collections.defaultdict(list)

    for lineno, _, _, error_message in err:
        errors[int(lineno)].append(error_message)

    code = code.replace('\t', '    ').split('\n')
    formatter = pygments.formatters.HtmlFormatter(
        style="emacs", cssclass="codehilite")
    css_string = "<style>" + formatter.get_style_defs() + "</style>"

    prefix = '<div class="codehilite"><pre>'
    suffix = '</pre></div>\n'

    css_string += prefix

    for lineno in range(len(code)):
        line = code[lineno]

        highlighted = pygments.highlight(line, pygments.lexers.PythonLexer(), formatter)[
            len(prefix):-len(suffix)]

        if lineno + 1 in errors:
            all_errors = '\n'.join(errors[lineno + 1])
            highlighted = f"<a href=\"#\" title=\"{all_errors}\" data-toggle=\"tooltip\" data-placement=\"top\" style=\"background-color:#ffcccc;\">{highlighted}</a>"

        css_string += highlighted

    css_string += suffix
    return css_string


def compile_results(res):
    """Compile results into models.

    Input 'res' is in format: {question1: ["Passed", "Error", ...], question2: [...]}
    Transformed output: {question1: {total_num: ..., passed_num: ..., reason: [...]}, question2: {...}}
    """

    compiled = {}
    for question in res:
        compiled[question] = {}

        compiled[question]['total_num'] = len(res[question])
        compiled[question]['passed_num'] = sum(
            [1 for case in res[question] if res[question][case] == "Passed"])
        compiled[question]['reason'] = res[question]

    return compiled


def check_session_file_parsable(uploaded):
    d = {}
    exec(uploaded, d)

    if 'TestCases' not in d:
        return False, "Can't find class TestCases in the uploaded file. Please look for instructions in session creation for details."

    try:
        dummy = d['TestCases']('DUMMY')

        parameters = dummy.parameters
        answers = dummy.answers
    except Exception as e:
        return False, f"Can't parse class TestCases due to error {e}"

    if parameters.keys() != answers.keys():
        return False, f"The keys of parameters are different from the keys of answers."
    elif any(len(parameters[k]) != len(answers[k]) for k in answers.keys()):
        return False, f"The number of test cases are incompatiable between parameters and answers."
    elif any(not isinstance(case, tuple) for k in parameters.keys() for case in parameters[k]):
        return False, f"Some of the parameters are not wrapped in tuple."
    else:
        for k in parameters.keys():
            for i in range(len(parameters[k]) - 1):
                if len(parameters[k][i]) != len(parameters[k][i + 1]):
                    return False, f"The number of parameters for question {k} is inconsistent."

    return True, ""
