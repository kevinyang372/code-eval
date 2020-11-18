from RestrictedPython import compile_restricted_exec, safe_globals, limited_builtins, utility_builtins
from RestrictedPython.PrintCollector import PrintCollector
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.Guards import guarded_iter_unpack_sequence, guarded_unpack_sequence

from restricted_guard import get_safe_globals

import collections
import numpy as np
import multiprocess
from pathos.pools import ProcessPool


def getResult(function_lib, function_name, params):
    if function_name not in function_lib:
        return (1, f"Function {function_name} not found")
    try:
        result = function_lib[function_name](*params)
        return (0, result)
    except Exception as e:
        return (1, str(e))


class TimeoutException(Exception):
    pass


class BaseTest(object):

    def __init__(self, func):
        self.func = func

    def test(self, runtime, blacklist):
        result = {}
        for entry_point in self.parameters:
            result[entry_point] = self._test_question(
                runtime, entry_point, blacklist)
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

        def _hook_write(obj):
            return obj

        safe_globals = get_safe_globals()
        safe_globals['_print_'] = PrintCollector
        safe_globals['_getiter_'] = default_guarded_getiter
        safe_globals['_iter_unpack_sequence_'] = guarded_iter_unpack_sequence
        safe_globals['_unpack_sequence_'] = guarded_unpack_sequence
        safe_globals['_getitem_'] = _hook_getitem
        safe_globals['_write_'] = _hook_write
        safe_globals['list'] = list
        safe_globals['np'] = np

        for item in blacklist:
            if item in list(safe_globals.keys()):
                safe_globals.pop(item)

        safe_locals = safe_globals.copy()
        try:
            exec(byte_code.code, safe_locals)
        except Exception as e:
            for ind in range(len(self.parameters[entry_point])):
                errs[ind] = str(e)
            return errs

        for i, params in enumerate(self.parameters[entry_point]):

            p = ProcessPool()

            # make sure process will initialize
            p.terminate()
            p.restart()

            res = p.amap(getResult, [safe_locals], [entry_point], [params])

            try:
                result = res.get(timeout=runtime)[0]
            except multiprocess.context.TimeoutError as e:
                result = (1, "Time Out")

            p.close()
            p.join()

            def compare_lists(a, b):
                if not isinstance(a, (list, np.ndarray)) and not isinstance(b, (list, np.ndarray)):
                    if isinstance(a, (float, np.float64)) and isinstance(b, (float, np.float64)):
                        return np.isclose(a, b, rtol=1e-05, atol=1e-08, equal_nan=False)
                    return a == b
                if type(a) != type(b):
                    return False
                if len(a) == len(b) == 0:
                    return True
                if len(a) != len(b):
                    return False
                return all(map(compare_lists, a, b))

            if result[0] == 1:
                errs[str(params)] = result[1]
            elif compare_lists(result[1], self.answers[entry_point][i]):
                errs[str(params)] = "Passed"
            else:
                errs[str(params)] = f"Wrong Answer: {result[1]}"

        return errs
