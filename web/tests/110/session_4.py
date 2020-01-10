from base import BaseTest

class TestCases(BaseTest):

    def __init__(self, func):
        super().__init__(func)
        self.parameters = [(1, 2), (2, 1), (3, 3), (5, 2)]
        self.answers = [1, 2, 27, 25]