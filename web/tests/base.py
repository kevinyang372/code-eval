from RestrictedPython import compile_restricted_exec, safe_builtins

class BaseTest(object):

    def __init__(self, func):
        self.func = func
        
    def test(self):
        
        errs = {}

        byte_code = compile_restricted_exec(
            self.func,
            filename='<inline code>'
        )

        safe_locals = {}
        exec(byte_code.code, {}, safe_locals)

        for i, params in enumerate(self.parameters):
            try:
                temp = safe_locals['entry'](*params)
                if temp != self.answers[i]:
                    errs[i] = "Wrong Answers"
            except Exception as e:
                errs[i] = str(e)

        return errs