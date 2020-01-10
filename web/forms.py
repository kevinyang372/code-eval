from flask_wtf import FlaskForm
from wtforms import SelectField, FileField, BooleanField, SubmitField, PasswordField, StringField, DecimalField, IntegerField
from wtforms.validators import InputRequired, DataRequired

class CodeSumitForm(FlaskForm):
    filename = FileField()
    sessions = SelectField('Choose Sessions', coerce = str)
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign in')

class UploadForm(FlaskForm):
    filename = FileField()
    session_num = IntegerField('Session Number', validators=[DataRequired()])
    seminar_num = SelectField('Choose Seminar', coerce = str)
    runtime = DecimalField('Run Time', default = 1.0)
    entry_point = StringField('Entry Point', default = 'entry')
    blacklist = StringField('Blacklist', default = '')
    submit = SubmitField('Submit')

class AddSeminar(FlaskForm):
    seminar_num = StringField('Seminar', validators=[DataRequired()])
    submit = SubmitField('Submit')