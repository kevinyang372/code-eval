from RestrictedPython import compile_restricted_exec, safe_globals
from RestrictedPython.PrintCollector import PrintCollector
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.Guards import guarded_iter_unpack_sequence

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
        safe_globals['_print_'] = PrintCollector
        safe_globals['_getiter_'] = default_guarded_getiter
        safe_globals['_iter_unpack_sequence_'] = guarded_iter_unpack_sequence

        exec(byte_code.code, safe_globals, safe_locals)

        for i, params in enumerate(self.parameters):
            try:
                temp = safe_locals['entry'](*params)
                if temp != self.answers[i]:
                    errs[i] = "Wrong Answers"
            except Exception as e:
                errs[i] = str(e)

        return errs