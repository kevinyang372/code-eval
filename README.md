# CodeEval

## Build
The application could be build with Docker

First navigate to the project root directory and build the image:

    $ docker build -t code_eval:latest .
    
After build completes, we can run the container:

    $ docker run -d -p 5000:5000 code_eval

## Sample Login Credentials
Default Admin
> Email: example_admin_user@gmail.com </br>
> Password: 111

Default User
> Email: example_user@gmail.com </br>
> Password: 111

## Functionality (Student)

### Join Course
To join a course, students need to first visit the link `localhost:5000/register/<course_invitation>` to gain access for code submissions. 

(By default visit `localhost:5000/register/join156` to add CS156.)

### Submit Code
To submit a valid code, students need to create an entry function for tester to run (by default the entry function is named 'entry') and return the correct result according to instructions.

(You could refer to [this](https://github.com/kevinyang372/codeEval/blob/master/sample.py) sample file which does a simple add function.)

## Functionality (Professor)

### Submit Code
< Same as Above >

### Summary
Professors can view a summary of student submissions to each course and session.

The summary is structured as `Index >> Course >> Session >> Student >> Submissions >> Result` .

### Upload Session
Upload a new session to a specific course.

**Required parameters:**
* Filename: A file consisting of all test cases.

Example:
```python
# import BaseTest is necessary for integration
from base import BaseTest

class TestCases(BaseTest):

    def __init__(self, func):
        super().__init__(func)
        
        # parameters should have the same length as answers
        self.parameters = [(1, 2), (3, 4), (7, 10), (5, 6)]
        self.answers = [3, 7, 17, 11]
```
* Session Number: Should be a positive decimal (e.g. 1.1).
* Course: Choose from available courses.
* Entry Point: Entry function to run in student submissions.
* Blacklist: Libraries that students should not use in submissions.

### Add Course
Add a new course and create a registration link for that course.

### All Settings
View / Modify / Delete courses and sessions.
