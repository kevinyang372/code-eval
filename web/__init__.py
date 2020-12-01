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

app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["FILE_UPLOADS"] = "web/tmp"
app.config["SESSION_UPLOADS"] = "web/tests"
app.config["ALLOWED_EXTENSIONS"] = ["py", "ipynb"]
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024
app.config['CODEMIRROR_LANGUAGES'] = ['python']
app.config['WTF_CSRF_ENABLED'] = True

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

from web import models

# add example user, seminar and session
db.create_all()
# example_admin = models.User(
#     id=1, email="example_admin_user@gmail.com", is_admin=True)
# example_admin.set_password("111")
# db.session.merge(example_admin)

# example_user = models.User(
#     id=2, email="example_user@gmail.com", is_admin=False)
# example_user.set_password("111")
# db.session.merge(example_user)

# example_user = models.User(
#     id=3, email="example_user_2@gmail.com", is_admin=False)
# example_user.set_password("111")
# db.session.merge(example_user)

# example_course = models.Course(id=1, course_num='CS156', registration="join156")
# db.session.merge(example_course)

# example_session = models.Session(id = 1, session_num=1.1, seminar_id=1, entry_point="entry", runtime=1.0, blacklist='')
# db.session.merge(example_session)
# db.session.commit()
