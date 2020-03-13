from base import BaseTest

class TestCases(BaseTest):

    def __init__(self, func):
        super().__init__(func)
        self.parameters = {
            'add': [(1, 2), (3, 4), (7, 10), (5, 6)],
            'subtract': [(1, 2), (3, 4), (7, 10), (5, 6)],
            'multiply': [(1, 2), (3, 4), (7, 10), (5, 6)]
        }
        self.answers = {
            'add': [3, 7, 17, 11],
            'subtract': [-1, -1, -3, -1],
            'multiply': [2, 12, 70, 30]
        }