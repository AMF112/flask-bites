from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField
from wtforms.validators import InputRequired, Email, Length


class RegisterForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[
            InputRequired(),
            Length(min=3, max=50, message='Username must be between 3 and 50 characters.')
        ]
    )
    email = EmailField(
        'Email',
        validators=[
            InputRequired(),
            Email(),
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            Length(min=8, message='Password must be at least 8 characters long.')
        ]
    )
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = EmailField(
        'Email',
        validators=[
            InputRequired(),
            Email(),
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            Length(min=8, message='Password must be at least 8 characters long.')
        ]
    )
    submit = SubmitField('Log In')

