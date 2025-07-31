from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, HiddenField
from wtforms.fields import DateField, TextAreaField, IntegerField, DateTimeLocalField

from wtforms.validators import DataRequired, Email, EqualTo, Length

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
    pdf_filename = StringField('PDF Filename (in static/pdfs/)')
    available_date = DateTimeLocalField('Available Date & Time (UTC)', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Create Issue')

class PuzzleForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    answer = StringField('Answer', validators=[DataRequired()])
    issue_id = SelectField('Issue', coerce=int)
    submit = SubmitField('Create Puzzle')

class HintForm(FlaskForm):
    puzzle_id = SelectField('Puzzle', coerce=int, validators=[DataRequired()])
    hint_text = TextAreaField('Hint Text', validators=[DataRequired()])
    unlock_date = DateField('Unlock Date', validators=[DataRequired()])
    submit = SubmitField('Add Hint')

