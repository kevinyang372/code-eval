import os
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
        self.test_login_admin();
        response = self.app.get('/summary', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # student access
    def test_student_access(self):
        self.test_login_student();
        response = self.app.get('/summary', follow_redirects=True)
        assert "You have no access to this page" in str(response.data)

if __name__ == '__main__':
    unittest.main()