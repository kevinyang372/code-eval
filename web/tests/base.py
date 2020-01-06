from RestrictedPython import compile_restricted_exec, safe_globals
from RestrictedPython.PrintCollector import PrintCollector
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.Guards import guarded_iter_unpack_sequence

from multiprocessing import Process

class TimeoutException(Exception): pass

class BaseTest(object):

    def __init__(self, func, timeout = 2):
        self.func = func
        self.timeout = timeout

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
                def getResult(r):
                    r.append(safe_locals['entry'](*params))

                result = []
                p = Process(target=getResult, args=(result,))
                p.start()
                p.join(self.timeout)

                if not result:
                    errs[i] = "Time Out"
                elif result[0] != self.answers[i]:
                    errs[i] = "Wrong Answers"
            except Exception as e:
                errs[i] = str(e)

        return errs