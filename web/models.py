from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin
from web import app, db, login
from datetime import datetime


class User(UserMixin, db.Model):
    """Data model for users."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200))
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean)
    results = db.relationship('Result', backref='user', lazy=True)
    courses = db.relationship('Course', secondary='access')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_num_submission(self, session_id):
        return sum(1 for result in self.results if result.session_id == session_id)


class Result(db.Model):
    """Data model for submission results."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String)
    passed_num = db.Column(db.Integer)
    runtime = db.Column(db.Float)
    success = db.Column(db.Boolean)
    content = db.Column(db.String)
    style_check = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey(
        'session.id'), nullable=False)
    questions = db.relationship('Question', cascade="all,delete",
                                backref='result', lazy=True)
    ts = db.Column(db.String)
    plagiarisms = db.relationship('Plagiarism',
                                  primaryjoin="or_(Result.id == Plagiarism.first_result_id, Result.id == Plagiarism.second_result_id)",
                                  cascade="all,delete", backref='result', lazy=True)

    def get_timedelta(self):
        """Get timedelta from current datetime."""
        current_time = datetime.utcnow()
        delta = current_time - datetime.strptime(self.ts, "%Y-%m-%d %H:%M:%S")
        return delta


class Question(db.Model):
    """Data model for tests."""
    id = db.Column(db.Integer, primary_key=True)
    passed_num = db.Column(db.Integer)
    name = db.Column(db.String)
    cases = db.relationship('Case', cascade="all,delete",
                            backref='result', lazy=True)
    result_id = db.Column(db.Integer, db.ForeignKey(
        'result.id'), nullable=False)


class Case(db.Model):
    """Data model for each individual test cases."""
    id = db.Column(db.Integer, primary_key=True)
    case_content = db.Column(db.String)
    success = db.Column(db.Boolean)
    reason = db.Column(db.String)
    question_id = db.Column(db.Integer, db.ForeignKey(
        'question.id'), nullable=False)


class Course(db.Model):
    """Data model for each course."""
    id = db.Column(db.Integer, primary_key=True)
    course_num = db.Column(db.String)
    registration = db.Column(db.String)
    sessions = db.relationship(
        'Session', cascade="all,delete", backref='course', lazy=True)
    users = db.relationship('User', secondary='access')


class Session(db.Model):
    """Data model for individual sessions in a course."""
    id = db.Column(db.Integer, primary_key=True)
    session_num = db.Column(db.Float)
    runtime = db.Column(db.Float)
    blacklist = db.Column(db.String)
    description = db.Column(db.String)
    course_id = db.Column(db.Integer, db.ForeignKey(
        'course.id'), nullable=False)
    results = db.relationship(
        'Result', cascade="all,delete", backref='session', lazy=True)
    test_code = db.Column(db.String)

    def get_blacklist(self):
        """Get a list of blacklisted packages."""
        return list(filter(lambda x: x != '', self.blacklist.split(',')))

    def get_submission_students(self):
        """Get a list of students who have submitted.

        The list is sorted with the students that haven't passed shown first and then those who passed.
        """
        return sorted(list(set(result.user for result in self.results)), key=lambda x: x in self.get_passed_submission_students())

    def get_passed_submissions(self):
        """Get a list of passed results."""
        return set(result for result in self.results if result.success)

    def get_passed_submission_students(self):
        """Get a list students who have submitted and passed."""
        return set(result.user for result in self.results if result.success)

    def get_passed_rate(self):
        """Get the passage rate for submissions."""
        if len(self.results) == 0:
            return 0.0
        return round(len(self.get_passed_submissions()) / len(self.results) * 100, 2)


class Access(db.Model):
    """Data model for the accessibility of a course."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey(
        'course.id'), nullable=False)

    user = db.relationship('User', backref=db.backref(
        "course", cascade="all, delete-orphan"))
    course = db.relationship('Course', backref=db.backref(
        "user", cascade="all, delete-orphan"))


class Codecacher(db.Model):
    """Data model for code caches."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'))
    text = db.Column(db.String)

    user = db.relationship('User', cascade="all,delete,delete-orphan",
                           backref='codecacher', lazy=True, single_parent=True)
    session = db.relationship('Session', cascade="all,delete,delete-orphan",
                              backref='codecacher', lazy=True, single_parent=True)


class Plagiarism(db.Model):
    """Data model for plagiarism check results."""
    __tablename__ = 'plagiarism'

    id = db.Column(db.Integer, primary_key=True)
    exact_match = db.Column(db.Boolean)
    unifying_ast = db.Column(db.Boolean)
    ignore_variables = db.Column(db.Boolean)
    similarity = db.Column(db.Float)

    first_result_id = db.Column(db.Integer, db.ForeignKey(
        'result.id'), nullable=False)
    second_result_id = db.Column(db.Integer, db.ForeignKey(
        'result.id'), nullable=False)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
