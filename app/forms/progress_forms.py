"""
Progress and Accomplishment Forms for EngineerOS.
Provides form fields and validation for logging projects, courses, and achievements.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length


class AccomplishmentForm(FlaskForm):
    """Form for students to log achievements, projects, and certifications."""

    type = SelectField(
        'Accomplishment Type',
        choices=[
            ('project_completed', 'Project / Portfolio Work'),
            ('course_completed', 'Course / Online Certification'),
            ('skill_added', 'Skill Mastery / Technical Achievement')
        ],
        validators=[DataRequired(message='Please select the type of accomplishment.')]
    )

    title = StringField(
        'Title / Name',
        validators=[
            DataRequired(message='Please enter a title for your accomplishment.'),
            Length(min=3, max=200, message='Title must be between 3 and 200 characters.')
        ],
        render_kw={'placeholder': 'e.g. Built E-Commerce REST API with Flask & Docker'}
    )

    description = TextAreaField(
        'Description & Key Takeaways',
        validators=[Optional(), Length(max=1000, message='Description cannot exceed 1000 characters.')],
        render_kw={
            'placeholder': 'Brief summary of what you built, learned, or achieved...',
            'rows': 3
        }
    )

    skills_gained = StringField(
        'Skills Used / Gained',
        validators=[Optional(), Length(max=255, message='Skills list cannot exceed 255 characters.')],
        render_kw={'placeholder': 'e.g. Python, Docker, PostgreSQL, JWT Auth (comma-separated)'}
    )

    submit = SubmitField('Log Accomplishment')
