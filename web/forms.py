from flask_wtf import FlaskForm
from wtforms import SelectField, FileField, BooleanField, SubmitField
from wtforms.validators import InputRequired

class CodeSumitForm(FlaskForm):
    filename = FileField()
    sessions = SelectField('Choose Sessions', coerce = str)
    submit = SubmitField('Submit')