"""Base test class for running user submitted code in restricted/safe environment."""

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
    """Run the user submitted function against test cases and return the outcome."""

    # Check if the function is provided by the user code.
    if function_name not in function_lib:
        return (1, f"Function {function_name} not found")

    try:
        result = function_lib[function_name](*params)
        return (0, result)
    except Exception as e:
        # Return the exception if one is encountered when running the tests.
        return (1, str(e))


class TimeoutException(Exception):
    """Custom exception class for returning code execution time out errors."""
    pass


class BaseTest(object):
    """Base class each test case should inherit.

    To create a new test, one should inherit this class and initialize the 'parameters' and 'answers'
    dictionary with test parameters and correct answers accordingly. See sample_test.py for one example
    initiating the test.

    Provides the public 'test' method for the application to run tests with provided runtime constraint
    and blacklisted libraries.
    """

    def __init__(self, func):
        self.func = func

        # Parameters to initialize
        self.parameters = {}
        self.answers = {}

    def test(self, runtime, blacklist):
        """Method for running tests with runtime and blacklisted libraries constraints."""
        result = {}

        # Run each test individually.
        for entry_point in self.parameters:
            result[entry_point] = self._test_question(
                runtime, entry_point, blacklist)

        return result

    def _test_question(self, runtime, entry_point, blacklist):
        """Private method for running a specific test case."""

        # Compile user submitted code to a safe version with RestrictedPython.
        byte_code = compile_restricted_exec(
            self.func,
            filename='<inline code>'
        )
        errs = {}

        # Check if RestrictedPython could successfully parse the code.
        if not byte_code.code:
            for ind in range(len(self.parameters[entry_point])):
                errs[ind] = 'Failed to parse input'
            return errs

        # Initialize a list of builtins users should be able to use.
        # For more information check https://restrictedpython.readthedocs.io/en/latest/usage/api.html#restricted-builtins.
        def _hook_getitem(obj, attr):
            return obj.__getitem__(attr)

        def _hook_write(obj):
            return obj

        # Default Python builtins.
        safe_globals = get_safe_globals()
        safe_globals['_print_'] = PrintCollector
        safe_globals['_getiter_'] = default_guarded_getiter
        safe_globals['_iter_unpack_sequence_'] = guarded_iter_unpack_sequence
        safe_globals['_unpack_sequence_'] = guarded_unpack_sequence
        safe_globals['_getitem_'] = _hook_getitem
        safe_globals['_write_'] = _hook_write
        safe_globals['list'] = list

        # Some third-party dependencies users should be able to use.
        safe_globals['np'] = np

        # Remove blacklisted packages from builtins.
        for item in blacklist:
            if item in list(safe_globals.keys()):
                safe_globals.pop(item)

        safe_locals = safe_globals.copy()

        # Compile the parsed code and add any error in the compiling process to the err list.
        try:
            exec(byte_code.code, safe_locals)
        except Exception as e:
            for ind in range(len(self.parameters[entry_point])):
                errs[ind] = str(e)
            return errs

        # Iterate over each test case.
        for i, params in enumerate(self.parameters[entry_point]):

            p = ProcessPool()

            # Make sure process will initialize.
            p.terminate()
            p.restart()

            # Use multiprocess here to keep track of the runtime and terminate any that goes over the runtime.
            res = p.amap(getResult, [safe_locals], [entry_point], [params])

            try:
                result = res.get(timeout=runtime)[0]
            except multiprocess.context.TimeoutError as e:
                result = (1, "Time Out")

            # Properly close the process if it did not terminate clean.
            p.close()
            p.join()

            def compare_lists(a, b):
                """Utility method to compare the runtime results and provided answers."""

                if not isinstance(a, (tuple, list, np.ndarray)) and not isinstance(b, (tuple, list, np.ndarray)):
                    # Give a threshold for minimum difference between float point numbers.
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

            if result[0] == 1:  # 1 indicates that there is an error.
                errs[str(params)] = result[1]
            elif compare_lists(result[1], self.answers[entry_point][i]):
                errs[str(params)] = "Passed"
            else:
                errs[str(params)] = f"Wrong Answer: {result[1]}"

        return errs
