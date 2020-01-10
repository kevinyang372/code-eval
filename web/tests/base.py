from RestrictedPython import compile_restricted_exec, safe_globals, limited_builtins, utility_builtins
from RestrictedPython.PrintCollector import PrintCollector
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.Guards import guarded_iter_unpack_sequence

from multiprocessing import Process, Queue

class TimeoutException(Exception): pass

class BaseTest(object):

    def __init__(self, func):
        self.func = func

    def test(self, runtime, entry_point, blacklist):

        byte_code = compile_restricted_exec(
            self.func,
            filename='<inline code>'
        )

        safe_locals = {}
        safe_globals['_print_'] = PrintCollector
        safe_globals['_getiter_'] = default_guarded_getiter
        safe_globals['_iter_unpack_sequence_'] = guarded_iter_unpack_sequence
        safe_globals.update(limited_builtins)
        safe_globals.update(utility_builtins)

        for item in blacklist:
            if item in list(safe_globals.keys()):
                safe_globals.pop(item)

        exec(byte_code.code, safe_globals, safe_locals)

        errs = {}
        for i, params in enumerate(self.parameters):
            def getResult(r):
                try:
                    r.put((0, safe_locals[entry_point](*params)))
                except Exception as e:
                    r.put((1, e))

            result = Queue()
            p = Process(target=getResult, args=(result,))
            p.start()
            p.join(runtime)

            if result.empty():
                p.terminate()
                errs[i] = "Time Out"
            else:
                output = result.get()
                if output[0] == 1:
                    errs[i] = output[1]
                elif output[1] != self.answers[i]:
                    errs[i] = "Wrong Answers"
                else:
                    errs[i] = "Passed"

        return errs