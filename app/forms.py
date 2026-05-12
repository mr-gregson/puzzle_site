from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, HiddenField, BooleanField
from wtforms.fields import DateField, TextAreaField, IntegerField, DateTimeLocalField

from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
    display_name = StringField('Display Name', validators=[DataRequired(), Length(min=1, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AnswerForm(FlaskForm):
    answer = StringField('Your Answer', validators=[DataRequired()])
    submit = SubmitField('Submit Answer')

class IssueForm(FlaskForm):
    title = StringField('Issue Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    pdf_filename = StringField('PDF Filename (optional, in static/pdfs/)')
    answer_pdf_filename = StringField('Answer PDF Filename (optional, in static/pdfs/)')
    pdf_upload = FileField('Upload Issue PDF (.pdf)', validators=[Optional()])
    answer_pdf_upload = FileField('Upload Answer Key PDF (.pdf)', validators=[Optional()])
    available_date = DateTimeLocalField('Available Date & Time (UTC)', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Create Issue')

class PuzzleForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    answer = StringField('Answer', validators=[Optional()])
    correct_response = TextAreaField('Custom Correct Response', validators=[Optional(), Length(max=2000)])
    incorrect_response = TextAreaField('Custom Incorrect Response', validators=[Optional(), Length(max=2000)])
    issue_id = SelectField('Issue', coerce=int)
    submit = SubmitField('Create Puzzle')


class PuzzleAnswerRuleForm(FlaskForm):
    answer = StringField('Answer to Match', validators=[DataRequired(), Length(max=255)])
    feedback_text = TextAreaField('Feedback Message', validators=[Optional(), Length(max=2000)])
    outcome = SelectField(
        'Outcome Override',
        choices=[
            ('neutral', 'Do not override correctness'),
            ('correct', 'Treat this answer as correct'),
            ('incorrect', 'Treat this answer as incorrect'),
        ],
        default='neutral',
    )
    submit = SubmitField('Add Response Rule')

class HintForm(FlaskForm):
    puzzle_id = SelectField('Puzzle', coerce=int, validators=[DataRequired()])
    hint_text = TextAreaField('Hint Text', validators=[DataRequired()])
    unlock_date = DateField('Unlock Date', validators=[DataRequired()])
    submit = SubmitField('Add Hint')

class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class UserPreferencesForm(FlaskForm):
    display_name = StringField('Display Name', validators=[DataRequired(), Length(min=1, max=150)])
    email_notifications = BooleanField('Enable email notifications')
    notify_new_issues = BooleanField('Notify me when new issues become available')
    notify_new_hints = BooleanField('Notify me when new hints are unlocked for puzzles I\'ve attempted')
    submit = SubmitField('Update Preferences')

class ErrataForm(FlaskForm):
    title = StringField('Erratum Title', validators=[DataRequired()])
    description = TextAreaField('Erratum Description', validators=[DataRequired()])
    puzzle_id = SelectField('Related Puzzle (optional)', coerce=int)
    issue_id = SelectField('Related Issue (optional)', coerce=int) 
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Erratum')

