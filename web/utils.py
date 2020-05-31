from flask_login import current_user
from flask import redirect, url_for, flash, request, jsonify
from functools import wraps
from web import app
import os
import nbformat
from nbconvert import PythonExporter
import pygments
from web.models import User, Result
import json
import itertools
import ast
import difflib
from zss import simple_distance, Node
import collections


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


def highlight_diff_temp(file_contents):
    try:
        tree1 = ast.parse(file_contents[0])
        tree2 = ast.parse(file_contents[1])
    except Exception as e:
        return ['Could not parse Python file', 'Could not parse Python file']

    d = ast_match_wrapper(tree1, tree2)
    pre = '<style>.diff_plus { background-color: rgba(0, 255, 0, 0.3) }</style>'

    parsed1 = [pre] + file_contents[0].split('\n')
    parsed2 = [pre] + file_contents[1].split('\n')
    visited = set()

    for n1, nodes in d.items():
        for t in range(n1[0], n1[1] + 1):
            parsed1[t] = '<div class={}>{}</div>'.format('diff_plus', parsed1[t])
        for n2 in nodes:
            for j in range(n2[0], n2[1] + 1):
                if j not in visited:
                    parsed2[j] = '<div class={}>{}</div>'.format('diff_plus', parsed2[j])
                    visited.add(j)

    for instance in [parsed1, parsed2]:
        for i in range(1, len(instance)):
            if not instance[i].startswith('<div'):
                instance[i] = '<div>{}</div>'.format(instance[i])

    return parsed1, parsed2

def highlight_diff(file_names, file_contents):

    class Formatter(pygments.formatters.HtmlFormatter):
        def wrap(self, source, outfile):
            return source

    f = Formatter(style="emacs", cssclass="codehilite")
    colored = [pygments.highlight(fc, pygments.lexers.PythonLexer(), f).splitlines(keepends=True) for fc in file_contents]

    addition = '.codehilite .diff_plus { background-color: rgba(0, 255, 0, 0.3) }'
    deletion = '.codehilite .diff_minus { background-color: rgba(255, 0, 0, 0.3) }'
    special = '.codehilite .diff_special { background-color: rgba(128, 128, 128, 0.3) }'
    res = '<style>%s%s%s%s</style>' % (f.get_style_defs(), addition, deletion, special)

    res += '<pre class="codehilite">'
    c = 0

    for line in difflib.unified_diff(*(colored+file_names)):
        # For each line we output a <div> with the original content,
        # but if it starts with a special diff symbol, we apply a class to it
        cls = {'+': 'diff_plus', '-': 'diff_minus', '@': 'diff_special'}.get(line[:1], '')
        if cls: cls = ' class="{}"'.format(cls)
        line = '<div{}>{}</div>'.format(cls, line.rstrip('\n'))
        res += line
        c += 1

    if not c: return '<div>Two pieces of code are exactly the same</div>'
    
    res += '</pre>'
    return res


def compile_results(res):
    """compile results into models"""

    compiled = {}
    for question in res:
        compiled[question] = {}

        compiled[question]['total_num'] = len(res[question])
        compiled[question]['passed_num'] = sum([1 for case in res[question] if res[question][case] == "Passed"])
        compiled[question]['reason'] = res[question]

    return compiled


def compile_plagarism_report(code, user_id, session_id):

    results = Result.query.filter(Result.user_id != user_id, Result.session_id == session_id).all()

    try:
        tree1 = ast.parse(code)
    except Exception as e:
        return []
        
    res = []

    for result in results:
        try:
            tree2 = ast.parse(result.content)
        except Exception as e:
            continue

        comparison = [0] * 5
        comparison[0] = 1 if exact_match(tree1, tree2) else 0
        comparison[1] = 1 if unifying_ast_match(tree1, tree2) else 0
        comparison[2] = 1 if ast_match_ignoring_variables(tree1, tree2) else 0
        # comparison[3] = 1 if ast_match_reordering(tree1, tree2) else 0
        # comparison[3] = simple_distance((copyTree(tree1, None)), (copyTree(tree2, None)))

        res.append({'result': comparison, 'result_id': result.id})

    return res


def compile_plagarism_report_two(file_contents):
    try:
        tree1 = ast.parse(file_contents[0])
        tree2 = ast.parse(file_contents[1])
    except Exception as e:
        return []

    comparison = []
    comparison.append(exact_match(tree1, tree2))
    comparison.append(unifying_ast_match(tree1, tree2))
    comparison.append(ast_match_ignoring_variables(tree1, tree2))
    # comparison.append(ast_match_reordering(tree1, tree2))

    # node_1, node_2 = (copyTree(tree1, None)), (copyTree(tree2, None))
    # distance = simple_distance(node_1, node_2)
    # comparison.append(distance)

    # percentage = '%.3f' % (1 - float(distance) / max(getTreeSize(node_1), getTreeSize(node_2)))
    # comparison.append(percentage)

    return comparison


# Exact match between two pieces of code
def exact_match(node1, node2):
    if type(node1) is not type(node2):
        return False
    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in ('lineno', 'col_offset', 'ctx'):
                continue
            if not exact_match(v, getattr(node2, k)):
                return False

        return True
    elif isinstance(node1, list):
        return all(itertools.starmap(exact_match, zip(node1, node2)))
    else:
        return node1 == node2


# unifying ast match detecting naive variable renaming
def unifying_ast_match(node1, node2, mapping = {}):
    if type(node1) is not type(node2):
        return False
    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in ('lineno', 'col_offset', 'ctx'):
                continue

            if (k == 'id' or k == 'arg') and v != getattr(node2, k):
                if v not in mapping:
                    mapping[v] = getattr(node2, k)
                elif mapping[v] != getattr(node2, k):
                    return False
            elif not unifying_ast_match(v, getattr(node2, k), mapping):
                return False

        return True
    elif isinstance(node1, list):
        return all(itertools.starmap(unifying_ast_match, zip(node1, node2, mapping)))
    else:
        return node1 == node2


# ignore variables
def ast_match_ignoring_variables(node1, node2):
    if type(node1) is not type(node2):
        return False
    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in ('lineno', 'col_offset', 'ctx', 'id', 'arg'):
                continue
            elif not ast_match_ignoring_variables(v, getattr(node2, k)):
                return False

        return True
    elif isinstance(node1, list):
        return all(itertools.starmap(ast_match_ignoring_variables, zip(node1, node2)))
    else:
        return node1 == node2


# # reordering
# def ast_match_reordering(node1, node2):
#     if type(node1) is not type(node2):
#         return False
#     if isinstance(node1, ast.AST):
#         for k, v in vars(node1).items():
#             if k in ('lineno', 'col_offset', 'ctx', 'id', 'arg'):
#                 continue
#             elif not ast_match_reordering(v, getattr(node2, k)):
#                 return False

#         return True
#     elif isinstance(node1, list):
#         if len(node1) != len(node2): return False
#         return any(all(itertools.starmap(ast_match_reordering, zip(node1, i))) for i in itertools.permutations(node2))
#     else:
#         return node1 == node2


# ignore variable with line highlighting
def ast_match_wrapper(node1, node2):
    d = collections.defaultdict(set)
    def func(node1, node2, is_parent = True):
        if type(node1) is not type(node2):
            return False
        if isinstance(node1, ast.AST):

            next_parent = is_parent and 'lineno' not in vars(node1)

            for k, v in vars(node1).items():
                if k in ('lineno', 'col_offset', 'ctx', 'id', 'arg', 'name'):
                    continue
                elif not func(v, getattr(node2, k), next_parent):
                    return False

            if 'lineno' in vars(node1) and is_parent:
                if 'end_lineno' in vars(node1):
                    d[getattr(node1, 'lineno'), getattr(node1, 'end_lineno')].add((getattr(node2, 'lineno'), getattr(node2, 'end_lineno')))
                else:
                    d[getattr(node1, 'lineno'), getattr(node1, 'lineno')].add((getattr(node2, 'lineno'), getattr(node2, 'lineno')))

            return True
        elif isinstance(node1, list):
            if len(node1) <= len(node2):
                for i, n1 in enumerate(node1):
                    f = False
                    for di in range(-1, 2):
                        if 0 <= i + di < len(node2) and func(n1, node2[i + di]): f = True
                    
                    if not f: return  False

                return True

            else:
                for i, n2 in enumerate(node2):
                    f = False
                    for di in range(-1, 2):
                        if 0 <= i + di < len(node1) and func(node1[i + di], n2): f = True
                    
                    if not f: return False

                return True
        else:
            return node1 == node2

    res = func(node1, node2)
    return d


def copyTree(node, dummy):
    t = type(node).__name__

    if 'name' in node._fields:
        t += ':' + node.name
    elif 'id' in node._fields:
        t += ':' + node.id
    
    curr = Node(t)
    if dummy is not None: dummy.addkid(curr)

    for k, v in vars(node).items():
        if isinstance(v, list):
            for p in v:
                if isinstance(p, ast.AST):
                    copyTree(p, curr)
        elif isinstance(v, ast.AST):
            copyTree(v, curr)

    return curr


def getTreeSize(root):
    return 1 + sum(getTreeSize(node) for node in root.children)