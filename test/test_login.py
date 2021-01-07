import unittest
from test.basic import FlaskTestCase


class TestLoginCase(FlaskTestCase):

    # Login admin.
    def test_login_admin(self):
        response = self.login_as_admin()
        assert "Invalid username or password" not in str(response.data)

    # Login student.
    def test_login_student(self):
        response = self.login_as_student()
        assert "Invalid username or password" not in str(response.data)

    # Test admin logout.
    def test_logout_admin(self):
        self.login_as_admin()
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Test student logout.
    def test_logout_student(self):
        self.login_as_student()
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Admin access.
    def test_admin_access(self):
        self.login_as_admin()
        response = self.app.get('/summary', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Student access.
    def test_student_access(self):
        self.login_as_student()
        response = self.app.get('/summary', follow_redirects=True)
        assert "You have no access to this page" in str(response.data)


if __name__ == '__main__':
    unittest.main()
