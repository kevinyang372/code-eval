from flask_wtf import FlaskForm
from wtforms import SelectField, FileField, BooleanField, SubmitField, PasswordField, StringField, DecimalField, IntegerField
from wtforms.validators import DataRequired, Email, NumberRange, Regexp, Optional

class CodeSumitForm(FlaskForm):
    filename = FileField()
    sessions = SelectField('Choose Sessions', coerce = float)
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Email()])
    password = PasswordField('Password', validators=[DataRequired(message="Password is required")])
    submit = SubmitField('Sign in')

class UploadForm(FlaskForm):
    filename = FileField()
    session_num = DecimalField('Session Number', validators=[NumberRange(min=0.0, max=20.0, message='Session number must be a positive decimal')])
    course_num = SelectField('Choose Course', coerce = str)
    runtime = DecimalField('Run Time', default = 1.0, validators=[NumberRange(min=0.0, max=600.0, message='Runtime restriction must be a positive decimal')])
    entry_point = StringField('Entry Point (Name of the function to run)', default = 'entry', validators=[Regexp(regex=r'^[a-z|A-Z|_|\d+|-]+$', message="Entry function must not contain any spaces in between")])
    blacklist = StringField('Blacklist (List of packages to ban, separated by comma, no space in between)', default = '', validators=[Optional(), Regexp(regex=r'^[a-z|A-Z|_|\d+|-|,]+$', message="Entry function must not contain any spaces in between")])
    submit = SubmitField('Submit')

class AddCourse(FlaskForm):
    course_num = StringField('Course', validators=[DataRequired()])
    registration_link = StringField("Registration Link for Students ('/register/-link-')", validators=[Regexp(regex=r'^[a-z|A-Z|_|\d+|-]+$', message="Invitation link must have no / in between")])
    submit = SubmitField('Submit')