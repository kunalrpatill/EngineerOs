"""
Authentication Forms for EngineerOS.
Provides validation for Student Registration and Login.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User


class LoginForm(FlaskForm):
    """Form for existing students to log in."""
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message='Please enter your email address.'),
            Email(message='Please enter a valid email address.')
        ],
        render_kw={'placeholder': 'name@example.com', 'autocomplete': 'email'}
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Please enter your password.')
        ],
        render_kw={'placeholder': 'Enter your password', 'autocomplete': 'current-password'}
    )
    remember_me = BooleanField('Remember me on this device')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    """Form for new engineering students to create an account."""
    name = StringField(
        'Full Name',
        validators=[
            DataRequired(message='Please enter your full name.'),
            Length(min=2, max=100, message='Name must be between 2 and 100 characters.')
        ],
        render_kw={'placeholder': 'e.g. Kunal Sharma', 'autocomplete': 'name'}
    )
    email = StringField(
        'College / Personal Email',
        validators=[
            DataRequired(message='Please enter your email address.'),
            Email(message='Please enter a valid email address.'),
            Length(max=150, message='Email cannot exceed 150 characters.')
        ],
        render_kw={'placeholder': 'name@college.edu or name@gmail.com', 'autocomplete': 'email'}
    )
    password = PasswordField(
        'Create Password',
        validators=[
            DataRequired(message='Please create a password.'),
            Length(min=6, message='Password must be at least 6 characters long.')
        ],
        render_kw={'placeholder': 'At least 6 characters', 'autocomplete': 'new-password'}
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords do not match. Please re-enter.')
        ],
        render_kw={'placeholder': 'Re-enter your password', 'autocomplete': 'new-password'}
    )
    submit = SubmitField('Create Student Account')

    def validate_email(self, field):
        """Check if email is already registered in database."""
        user = User.query.filter_by(email=field.data.strip().lower()).first()
        if user:
            raise ValidationError('An account with this email address already exists. Please log in instead.')
