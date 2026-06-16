from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, FloatField, StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateTimeField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from datetime import datetime

class RegisterForm(FlaskForm):
    full_name = StringField('Full name', validators=[DataRequired(), Length(min=3, max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('Employee','Employee'),('HSE Officer','HSE Officer'),('Supervisor','Supervisor')], default='Employee')
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')  # this is the missing field
    submit = SubmitField('Login')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
    
class IncidentForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    department = SelectField("Department", choices=[("Administration","Administration"),("Production","Production"),("Quality Control","Quality Control"),("Field Operations","Field Operations"),("Finance","Finance"),("Logistics","Logistics")])
    type = SelectField("Type", choices=[("Near Miss","Near Miss"),("Spill","Spill"),("Injury","Injury"),("Fire","Fire"),("Falls","Falls"),("Cuts","Cuts"),("Equipment malfunctions","Equipment malfunctions"),("Electrical Injury","Electrical Injury"),("Struck by incident","Struck by incident")])
    man_hours = FloatField('Man Hours', default=0.0)
    people_affected = IntegerField('People Affected', default=0)
    date = DateField("Date", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    reported_at = DateTimeField('Reported At (YYYY-mm-dd HH:MM)', format='%Y-%m-%d %H:%M', default=datetime.utcnow)
    submit = SubmitField("Submit")
