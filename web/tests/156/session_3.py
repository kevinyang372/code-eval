from base import BaseTest

class TestCases(BaseTest):

    def __init__(self, func, timeout = 2):
        super().__init__(func, timeout)
        self.parameters = [(1, 2), (2, 1), (3, 3), (5, 2)]
        self.answers = [1, 2, 27, 25]