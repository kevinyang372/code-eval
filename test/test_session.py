import unittest
from test.basic import FlaskTestCase


class TestSessionCase(FlaskTestCase):

    # Post to main page.
    def test_mainpage(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Test create session.
    def test_create_session(self):
        response = self.create_session()
        self.assertEqual(response.status_code, 200)

    # Test delete session.
    def test_delete_session(self):
        self.create_session()

        response = self.app.get('/delete_session/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Test add course.
    def test_add_course(self):
        self.login_as_admin()

        response = self.app.post('/add_course', data = dict(course_num="CS166", registration_link="abcd"), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Test delete course.
    def test_delete_course(self):
        self.login_as_admin()

        response = self.app.get('/delete_course/2', follow_redirects=True)
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
