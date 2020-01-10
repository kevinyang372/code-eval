from base import BaseTest

class TestCases(BaseTest):

    def __init__(self, func):
        super().__init__(func)
        self.parameters = [(1, 2), (3, 4), (7, 10), (5, 6)]
        self.answers = [3, 7, 17, 11]