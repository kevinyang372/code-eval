import os
import io
import sys
import unittest

os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
from web import app, db

class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        self.app = app.test_client()

    def tearDown(self):
        pass

    ###############
    #### tests ####
    ###############

    # post to main page
    def test_mainpage(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # login admin
    def test_login_admin(self):
        response = self.app.post('login', data = dict(email="example_admin_user@gmail.com", password="111"), follow_redirects=True)
        assert "Invalid username or password" not in str(response.data)

    # login student
    def test_login_student(self):
        response = self.app.post('login', data = dict(email="example_user@gmail.com", password="111"), follow_redirects=True)
        assert "Invalid username or password" not in str(response.data)

    # admin access
    def test_admin_access(self):
        self.test_login_admin()
        response = self.app.get('/summary', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # student access
    def test_student_access(self):
        self.test_login_student()
        response = self.app.get('/summary', follow_redirects=True)
        assert "You have no access to this page" in str(response.data)

    # test create session
    def test_create_session(self):
        self.test_login_admin()

        to_test = ''
        with open('sample_test.py', 'r') as file:
            for line in file:
                to_test += line

        response = self.app.post('/upload_session', data = dict(filename=(io.BytesIO(to_test.encode()), 'test_sample.py'), session_num=1.1, course_num="CS156", runtime=1.0), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # test submitting files
    def test_upload_file(self):
        self.test_create_session()

        to_test = ''
        with open('sample.py', 'r') as file:
            for line in file:
                to_test += line

        response = self.app.post('/submit/1/1', data = dict(filename=(io.BytesIO(to_test.encode()), 'test.py')), follow_redirects=True)
        assert "Passed Test Cases: 3 / 3" in str(response.data)

    # test submitting malicious files
    def test_upload_malicious(self):
        self.test_create_session()

        import glob
        for filename in glob.glob('malicious/*'):
            to_test = ''
            with open(filename, 'r') as file:
                for line in file:
                    to_test += line

            response = self.app.post('/submit/1/1', data = dict(filename=(io.BytesIO(to_test.encode()), 'test.py')), follow_redirects=True)
            assert "Passed Test Cases: 3 / 3" not in str(response.data)

if __name__ == '__main__':
    unittest.main()