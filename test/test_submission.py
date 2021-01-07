import io
import glob
import unittest
from test.basic import FlaskTestCase


class TestSubmissionCase(FlaskTestCase):

    # Test submitting files.
    def test_upload_file(self):
        response = self.upload_file()
        assert "Passed Test Cases: 3 / 3" in str(response.data)

    # Test submitting malicious files.
    def test_upload_malicious(self):
        self.create_session()

        for filename in glob.glob('malicious/test_*.py'):
            to_test = ''
            with open(filename, 'r') as file:
                for line in file:
                    to_test += line

            response = self.app.post('/submit/1/1', data = dict(filename=(io.BytesIO(to_test.encode()), 'test.py')), follow_redirects=True)
            assert "Passed Test Cases: 3 / 3" not in str(response.data)


if __name__ == '__main__':
    unittest.main()
