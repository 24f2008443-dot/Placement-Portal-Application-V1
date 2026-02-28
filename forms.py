from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, DateField, FloatField
from wtforms import SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember')
    submit = SubmitField('Login')

class StudentRegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    college = StringField('College', validators=[Optional(), Length(max=120)])
    branch = StringField('Branch', validators=[Optional(), Length(max=120)])
    cgpa = FloatField('CGPA', validators=[Optional(), NumberRange(min=0, max=10)])
    submit = SubmitField('Register')

class StudentProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    college = StringField('College', validators=[Optional(), Length(max=120)])
    branch = StringField('Branch', validators=[Optional(), Length(max=120)])
    cgpa = FloatField('CGPA', validators=[Optional(), NumberRange(min=0, max=10)])
    resume = FileField('Upload Resume (PDF)', validators=[FileAllowed(['pdf'], 'PDF files only!')])
    submit = SubmitField('Update Profile')

class CompanyRegisterForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=240)])
    hr_contact = StringField('HR Contact', validators=[Optional(), Length(max=120)])
    website = StringField('Website', validators=[Optional(), Length(max=240)])
    email = StringField('Admin Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class DriveForm(FlaskForm):
    job_title = StringField('Job Title', validators=[DataRequired(), Length(max=240)])
    job_description = TextAreaField('Job Description', validators=[Optional()])
    eligibility = StringField('Eligibility', validators=[Optional(), Length(max=240)])
    salary = StringField('Salary Range', validators=[Optional(), Length(max=100)])
    location = StringField('Location', validators=[Optional(), Length(max=120)])
    application_deadline = DateField('Application Deadline', validators=[Optional()])
    submit = SubmitField('Create / Update Drive')

class ApplicationForm(FlaskForm):
    submit = SubmitField('Apply')
