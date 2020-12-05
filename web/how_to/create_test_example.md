# Creating New Tests

Below is an example test file for three easy questions: add, subtract and multiply.

```
from base import BaseTest

class TestCases(BaseTest):

    def __init__(self, func):
        super().__init__(func)
        self.parameters = {
            'add': [(2, 3), (4, 5), (6, 7)],
            'subtract': [(2, 3), (4, 5)],
            'multiply': [(2, 3), (4, 5), (6, 7)]
        }
        self.answers = {
            'add': [5, 9, 13],
            'subtract': [-1, -1],
            'multiply': [6, 20, 42]
        }
```

Now let's break it down to understand how to create new tests.

### Importing and Inheriting BaseTest
```
from base import BaseTest
```
The import statement is required for all test files. It allows you to use the functionalities of provided by the `BaseTest` class including testing in a safe environment, measure run time and compile the test result report.

```
class TestCases(BaseTest):

    def __init__(self, func):
        super().__init__(func)
        ...
```
This part should also always be fixed as well since AutoGrader will try to look for the `TestCases` class to read all the parameters and answers.

### Parameters and Answers
The customizable part contains two variables -- parameters and answers. Parameters represent the input user is going to receive in their submitted function and answers represent the expected output their function should give. The formatting for both should be a dictionary that looks like the following:
```
{
    question_1: [case_1, case_2, case_3 ...]
    question_2: [case_1, case_2, case_3 ...]
    ...
}
```

_Note: The number of cases do not have to be the same across different questions_.

Each case in the parameters should be wrapped in tuples no matter the number of input parameters. Furthermore, the type of variables in answers should also match that of the expected output (e.g. a list if the function outputs a list).

### Answer Precisions
For float type answers, AutoGrader uses the `numpy.isclose` to decide whether an output is close enough to the expected answer. The code looks like the following
```
np.isclose(a, b, rtol=1e-05, atol=1e-08, equal_nan=False)
```

For more information on `numpy.isclose`, check the official documentation [here](https://numpy.org/doc/stable/reference/generated/numpy.isclose.html).