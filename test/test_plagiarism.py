import io
import glob
import unittest
from test.basic import FlaskTestCase

from web.models import Result  # noqa


class TestPlagiarismCase(FlaskTestCase):

    # Test plagiarism module.
    def test_upload_malicious(self):
        self.create_session()

        files = glob.glob('malicious/plagiarism_test_*.py')

        to_test = ''
        with open(files[0], 'r') as file:
            for line in file:
                to_test += line

        self.app.post('/submit/1/1', data = dict(filename=(io.BytesIO(to_test.encode()), 'test.py')), follow_redirects=True)

        # Get the result id from last submission.
        rid_1 = Result.query.filter_by(user_id=1).all()[-1].id

        self.logout()
        self.login_as_student()

        # Register for the course.
        self.app.get('/register/join156', follow_redirects=True)

        to_test = ''
        with open(files[1], 'r') as file:
            for line in file:
                to_test += line

        self.app.post('/submit/1/1', data = dict(filename=(io.BytesIO(to_test.encode()), 'test.py')), follow_redirects=True)

        # Get the result id from last submission.
        rid_2 = Result.query.filter_by(user_id=2).all()[-1].id

        self.logout()
        self.login_as_admin()

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
