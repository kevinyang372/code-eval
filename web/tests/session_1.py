class TestCases(object):

    def __init__(self, func):
        self.func = func
        self.parameters = [(1, 2), (3, 4), (7, 10), (5, 6)]
        self.answers = [3, 7, 17, 11]

    def test(self):
        
        errs = {}

        for i, params in enumerate(self.parameters):
            try:
                temp = self.func(*params)
                if temp != self.answers[i]:
                    errs[i] = "Wrong Answers"
            except Exception as e:
                errs[i] = str(e)

        return errs