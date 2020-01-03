class BaseTest(object):

    def __init__(self, func):
        self.func = func
        
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