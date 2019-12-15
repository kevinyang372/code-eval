import unittest
import requests

class FlaskTestCase(unittest.TestCase):

    def test_endpoint(self):
        r = requests.get('http://127.0.0.1:5000/')
        self.assertEqual(r.status_code, 200)

if __name__ == '__main__':
    unittest.main()