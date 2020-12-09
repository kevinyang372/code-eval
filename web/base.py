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


def getResult(code_block, function_name, params, blacklist):
    """Run the user submitted function against test cases and return the outcome."""

    # Check if the function is provided by the user code.

    safe_locals = {}

    # Get all safe builtins
    safe_globals = get_safe_globals()

    # Some third-party dependencies users should be able to use.
    safe_globals['np'] = np

    # Delete blacklisted packages.
    for item in blacklist:
        if item in list(safe_globals.keys()):
            safe_globals.pop(item)

    try:
        exec(code_block, safe_globals, safe_locals)
    except Exception as e:
        return (1, str(e))

    if function_name not in safe_locals:
        return (1, f"Function {function_name} not found")

    try:
        result = safe_locals[function_name](*params)
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

        # Iterate over each test case.
        for i, params in enumerate(self.parameters[entry_point]):

            p = ProcessPool()

            # Make sure process will initialize.
            p.terminate()
            p.restart()

            # Use multiprocess here to keep track of the runtime and terminate any that goes over the runtime.
            res = p.amap(getResult, [byte_code.code], [entry_point], [params], [blacklist])

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
