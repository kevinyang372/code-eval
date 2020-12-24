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
        pass

    ###############
    #### tests ####
    ###############

    # Post to main page.
    def test_mainpage(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Login admin.
    def test_login_admin(self):
        response = self.app.post('login', data = dict(email="example_admin_user@gmail.com", password="111"), follow_redirects=True)
        assert "Invalid username or password" not in str(response.data)

    # Login student.
    def test_login_student(self):
        response = self.app.post('login', data = dict(email="example_user@gmail.com", password="111"), follow_redirects=True)
        assert "Invalid username or password" not in str(response.data)

    # Test admin logout.
    def test_logout_admin(self):
        self.test_login_admin()
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Test student logout.
    def test_logout_student(self):
        self.test_login_student()
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Admin access.
    def test_admin_access(self):
        self.test_login_admin()
        response = self.app.get('/summary', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Student access.
    def test_student_access(self):
        self.test_login_student()
        response = self.app.get('/summary', follow_redirects=True)
        assert "You have no access to this page" in str(response.data)

    # Test create session.
    def test_create_session(self):
        self.test_login_admin()

        to_test = ''
        with open('sample_test.py', 'r') as file:
            for line in file:
                to_test += line

        response = self.app.post('/upload_session', data = dict(filename=(io.BytesIO(to_test.encode()), 'test_sample.py'), description="test", session_num=1.1, course_num="CS156", runtime=1.0), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Test delete session.
    def test_delete_session(self):
        self.test_create_session()

        response = self.app.get('/delete_session/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Test add course.
    def test_add_course(self):
        self.test_login_admin()

        response = self.app.post('/add_course', data = dict(course_num="CS166", registration_link="abcd"), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Test delete course.
    def test_delete_course(self):
        self.test_add_course()

        response = self.app.get('/delete_course/2', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Test submitting files.
    def test_upload_file(self):
        self.test_create_session()

        to_test = ''
        with open('sample.py', 'r') as file:
            for line in file:
                to_test += line

        response = self.app.post('/submit/1/1', data = dict(filename=(io.BytesIO(to_test.encode()), 'test.py')), follow_redirects=True)
        assert "Passed Test Cases: 3 / 3" in str(response.data)

    # Test submitting malicious files.
    def test_upload_malicious(self):
        self.test_create_session()

        for filename in glob.glob('malicious/test_*.py'):
            to_test = ''
            with open(filename, 'r') as file:
                for line in file:
                    to_test += line

            response = self.app.post('/submit/1/1', data = dict(filename=(io.BytesIO(to_test.encode()), 'test.py')), follow_redirects=True)
            assert "Passed Test Cases: 3 / 3" not in str(response.data)

    # Test apis get score.
    def test_apis_get_score(self):
        self.test_upload_file()

        response = self.app.post('/apis/get_score/example_admin_user@gmail.com/1', data = json.dumps({"credentials": {"email": "example_admin_user@gmail.com", "password": "111"}}), content_type='application/json')

        self.assertEqual(response.status_code, 200)

    # Test apis get file.
    def test_apis_submit_file(self):
        self.test_create_session()

        to_test = ''
        with open('sample.py', 'r') as file:
            for line in file:
                to_test += line

        response = self.app.post('/apis/submit/1', data = dict(file=(io.BytesIO(to_test.encode()), 'test.py'), email="example_admin_user@gmail.com", password="111"))

        self.assertEqual(response.status_code, 200)

    # Test plagiarism module.
    def test_upload_malicious(self):
        self.test_create_session()

        files = glob.glob('malicious/plagiarism_test_*.py')

        to_test = ''
        with open(files[0], 'r') as file:
            for line in file:
                to_test += line

        self.app.post('/submit/1/1', data = dict(filename=(io.BytesIO(to_test.encode()), 'test.py')), follow_redirects=True)

        # Get the result id from last submission.
        rid_1 = Result.query.filter_by(user_id=1).all()[-1].id

        self.test_logout_admin()
        self.test_login_student()

        # Register for the course.
        self.app.get('/register/join156', follow_redirects=True)

        to_test = ''
        with open(files[1], 'r') as file:
            for line in file:
                to_test += line

        self.app.post('/submit/1/1', data = dict(filename=(io.BytesIO(to_test.encode()), 'test.py')), follow_redirects=True)

        # Get the result id from last submission.
        rid_2 = Result.query.filter_by(user_id=2).all()[-1].id

        self.test_logout_student()
        self.test_login_admin()

        response = self.app.get('/plagiarism/1', follow_redirects=True)
        assert 'Case Similarity: 1.0' in str(response.data)

        response = self.app.get(f'/compare/{rid_1}/{rid_2}', follow_redirects=True)

        # strip spaces and new lines
        processed = response.data.decode('utf-8').replace(" ", "").replace("\n", "")

        assert "<td>UnifyingAST</td><td>True</td>" in processed  # verify whether unifying AST test passed
        assert "<td>Ignorevariables</td><td>True</td>" in processed  # verify whether ignore variables test passed
        assert "<td>ExactMatch</td><td>False</td>" in processed  # verify whether exact match test failed


if __name__ == '__main__':
    unittest.main()
