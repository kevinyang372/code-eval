from RestrictedPython import compile_restricted_exec, safe_globals, limited_builtins, utility_builtins
from RestrictedPython.PrintCollector import PrintCollector
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.Guards import guarded_iter_unpack_sequence

import numpy as np
from multiprocessing import Process, Queue
import collections


class TimeoutException(Exception):
    pass


class BaseTest(object):

    def __init__(self, func):
        self.func = func

    def test(self, runtime, blacklist):
        result = {}
        for entry_point in self.parameters:
            result[entry_point] = self._test_question(runtime, entry_point, blacklist)
        return result

    def _test_question(self, runtime, entry_point, blacklist):

        byte_code = compile_restricted_exec(
            self.func,
            filename='<inline code>'
        )
        errs = {}

        if not byte_code.code:
            for ind in range(len(self.parameters[entry_point])):
                errs[ind] = 'Failed to parse input'
            return errs

        def _hook_getitem(obj, attr):
            return obj.__getitem__(attr)

        safe_locals = {}
        safe_globals['_print_'] = PrintCollector
        safe_globals['_getiter_'] = default_guarded_getiter
        safe_globals['_iter_unpack_sequence_'] = guarded_iter_unpack_sequence
        safe_globals['_getitem_'] = _hook_getitem
        safe_globals['np'] = np

        for item in blacklist:
            if item in list(safe_globals.keys()):
                safe_globals.pop(item)

        try:
            exec(byte_code.code, safe_globals, safe_locals)
        except Exception as e:
            for ind in range(len(self.parameters[entry_point])):
                errs[ind] = str(e)
            return errs

        for i, params in enumerate(self.parameters[entry_point]):
            def getResult(r):
                try:
                    r.put((0, safe_locals[entry_point](*params)))
                except Exception as e:
                    r.put((1, str(e)))

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
                elif isinstance(output[1], (list, np.ndarray)):
                    if all(output[1] == self.answers[entry_point][i]):
                        errs[i] = "Passed"
                    else:
                        errs[i] = "Wrong Answers"
                elif output[1] != self.answers[entry_point][i]:
                    errs[i] = "Wrong Answers"
                else:
                    errs[i] = "Passed"

        return errs
