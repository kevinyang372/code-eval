from flask_login import current_user
from flask import redirect, url_for
from functools import wraps
from web import app
import os


def read_file(file, filename):
    file.save(os.path.join(app.config["FILE_UPLOADS"], filename))

    content = []
    with open(os.path.join(app.config["FILE_UPLOADS"], filename), 'r') as file:
        for line in file:
            content.append(line)

    os.remove(os.path.join(app.config["FILE_UPLOADS"], filename))
    return ''.join(content)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user or not current_user.is_admin:
            return redirect(url_for('index.index'))
        return f(*args, **kwargs)
    return decorated_function
