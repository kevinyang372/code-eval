import os
import io
import sys
import json
import glob
import unittest

os.environ["DATABASE_URL"] = "sqlite:///test.db"

from web import app, db, models  # noqa
from web.models import Result  # noqa


class FlaskTestCase(unittest.TestCase):

    def setUp(self):

        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False

        db.create_all()

        example_admin = models.User(
            id=1, email="example_admin_user@gmail.com", is_admin=True)
        example_admin.set_password("111")
        db.session.merge(example_admin)

        example_user = models.User(
            id=2, email="example_user@gmail.com", is_admin=False)
        example_user.set_password("111")
        db.session.merge(example_user)

        example_user = models.User(
            id=3, email="example_user_2@gmail.com", is_admin=False)
        example_user.set_password("111")
        db.session.merge(example_user)

        example_course = models.Course(id=1, course_num='CS156', registration="join156")
        db.session.merge(example_course)

        to_test = ''
        with open('sample_test.py', 'r') as file:
            for line in file:
                to_test += line

        example_session = models.Session(id=1, session_num=1.1, course_id=1, test_code=to_test, runtime=1.0, blacklist='')
        db.session.merge(example_session)
        db.session.commit()

        self.app = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login_as_admin(self):
        return self.app.post('login', data = dict(email="example_admin_user@gmail.com", password="111"), follow_redirects=True)

    def login_as_student(self):
        return self.app.post('login', data = dict(email="example_user@gmail.com", password="111"), follow_redirects=True)

    def logout(self):
        self.app.get('/logout', follow_redirects=True)

    def create_session(self):
        self.login_as_admin()

        to_test = ''
        with open('sample_test.py', 'r') as file:
            for line in file:
                to_test += line

        response = self.app.post('/upload_session', data = dict(filename=(io.BytesIO(to_test.encode()), 'test_sample.py'), description="test", session_num=1.1, course_num="CS156", runtime=1.0), follow_redirects=True)
        return response

    def upload_file(self):
        self.create_session()

        to_test = ''
        with open('sample.py', 'r') as file:
            for line in file:
                to_test += line

        response = self.app.post('/submit/1/1', data = dict(filename=(io.BytesIO(to_test.encode()), 'test.py')), follow_redirects=True)
        return response
