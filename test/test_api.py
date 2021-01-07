import io
import json
import unittest
from test.basic import FlaskTestCase


class TestAPICase(FlaskTestCase):

    # Test apis get score.
    def test_apis_get_score(self):
        self.upload_file()

        response = self.app.post('/apis/get_score/example_admin_user@gmail.com/1', data = json.dumps({"credentials": {"email": "example_admin_user@gmail.com", "password": "111"}}), content_type='application/json')

        self.assertEqual(response.status_code, 200)

    # Test apis get file.
    def test_apis_submit_file(self):
        self.create_session()

        to_test = ''
        with open('sample.py', 'r') as file:
            for line in file:
                to_test += line

        response = self.app.post('/apis/submit/1', data = dict(file=(io.BytesIO(to_test.encode()), 'test.py'), email="example_admin_user@gmail.com", password="111"))

        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
