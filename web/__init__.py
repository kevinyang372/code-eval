from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["FILE_UPLOADS"] = "web/tmp"
app.config["SESSION_UPLOADS"] = "web/tests"
app.config["ALLOWED_EXTENSIONS"] = ["py", "ipynb"]

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bootstrap = Bootstrap(app)
login = LoginManager(app)
login.login_view = 'login'

from web import routes, models

# add example user, seminar and session
db.create_all()
example_admin = models.User(id=1, email="example_admin_user@gmail.com", is_admin=True)
example_admin.set_password("111")
db.session.merge(example_admin)

example_user = models.User(id=2, email="example_user@gmail.com", is_admin=False)
example_user.set_password("111")
db.session.merge(example_user)

example_seminar = models.Seminar(id=1, seminar_num=156, registration="join156")
db.session.merge(example_seminar)

example_session = models.Session(id = 1, session_num=1.1, seminar_id=1, entry_point="entry", runtime=1.0, blacklist='')
db.session.merge(example_session)
db.session.commit()