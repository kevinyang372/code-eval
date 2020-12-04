from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_breadcrumbs import Breadcrumbs
from flask_codemirror import CodeMirror
import os
import sys

sys.path.append('web')
app = Flask(__name__)

# Configuration for the application.
app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["FILE_UPLOADS"] = "web/tmp"
app.config["SESSION_UPLOADS"] = "web/tests"
app.config["ALLOWED_EXTENSIONS"] = ["py", "ipynb"]
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024
app.config['CODEMIRROR_LANGUAGES'] = ['python']
app.config['WTF_CSRF_ENABLED'] = True

# Initialize the dependencies for Flask app.
csrf = CSRFProtect()
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bootstrap = Bootstrap(app)
login = LoginManager(app)
login.login_view = 'login.login'
csrf.init_app(app)
codemirror = CodeMirror(app)
Breadcrumbs(app=app)

from blueprints.settings import setting_template
from blueprints.sessions import session_template
from blueprints.login import login_template
from blueprints.courses import course_template
from blueprints.summary import summary_template
from blueprints.index import index_template
from blueprints.submissions import submission_template
from blueprints.apis import api_template
from blueprints.error import error_template
from blueprints.compare import compare_template
from blueprints.static import static_template

# Register the blueprints.
app.register_blueprint(index_template)
app.register_blueprint(summary_template)
app.register_blueprint(course_template)
app.register_blueprint(login_template)
app.register_blueprint(session_template)
app.register_blueprint(setting_template)
app.register_blueprint(submission_template)
app.register_blueprint(api_template, url_prefix="/apis")
app.register_blueprint(error_template)
app.register_blueprint(compare_template)
app.register_blueprint(static_template)

from web import models

# Create the database if it does not exist yet.
db.create_all()