from base import BaseTest

class TestCases(BaseTest):

    def __init__(self, func, timeout = 2):
        super().__init__(func, timeout)
        self.parameters = [(1, 2), (3, 4), (7, 10), (5, 6)]
        self.answers = [2, 12, 70, 30]