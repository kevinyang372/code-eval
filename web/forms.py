from flask_wtf import FlaskForm
from wtforms import SelectField, FileField, BooleanField, SubmitField, PasswordField, StringField, DecimalField, IntegerField
from wtforms.validators import DataRequired, Email, NumberRange, Regexp, Optional, ValidationError
from flask_codemirror.fields import CodeMirrorField
from web.models import Course, Session


class CodeSumitForm(FlaskForm):
    """Code submission form for students."""
    filename = FileField()
    text = CodeMirrorField(language='python', config={'lineNumbers': 'true'})   # CodeMirror plugin here.
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('Email', validators=[Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(message="Password is required")])
    submit = SubmitField('Sign in')


class UploadForm(FlaskForm):
    """Create a new session."""
    filename = FileField()
    session_num = DecimalField('Session Number', validators=[NumberRange(
        min=0.0, max=20.0, message='Session number must be a positive decimal')])
    course_num = SelectField('Choose Course', coerce=str)
    description = StringField(
        'Description of the question', validators=[DataRequired()])
    runtime = DecimalField('Run Time', default=1.0, validators=[NumberRange(
        min=0.0, max=600.0, message='Runtime restriction must be a positive decimal')])
    blacklist = StringField('Blacklist (List of packages to ban, separated by comma, no space in between)', default='', validators=[
                            Optional(), Regexp(regex=r'^[a-z|A-Z|_|\d+|-|,]+$', message="Entry function must not contain any spaces in between")])
    submit = SubmitField('Submit')

    def validate(self):
        """Validation against the database."""
        if not FlaskForm.validate(self):
            return False
        course_id = Course.query.filter_by(
            course_num=self.course_num.data).first().id
        session = Session.query.filter_by(
            course_id=course_id, session_num=self.session_num.data).first()

        if session:
            self.session_num.errors.append(
                "That session number is taken. Please choose another.")
            return False

        return True


class AddCourse(FlaskForm):
    """Add course form."""
    course_num = StringField('Course', validators=[DataRequired()])
    registration_link = StringField("Registration Link for Students ('/register/-link-')", validators=[
                                    Regexp(regex=r'^[a-z|A-Z|_|\d+|-]+$', message="Invitation link must have no / in between")])
    submit = SubmitField('Submit')

    def validate_course_num(form, field):
        """Validation against the database."""
        course = Course.query.filter_by(course_num=field.data).first()
        if course:
            raise ValidationError(
                'That course number is taken. Please choose another.')


class FilterResult(FlaskForm):
    """Filter result for plagiarism report."""
    threshold = DecimalField('Threshold', validators=[NumberRange(
        min=0.0, max=1.0, message='Threshold must be between 0 and 1')])
    submit = SubmitField('Submit')
