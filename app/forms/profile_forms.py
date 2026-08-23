"""
Profile Forms for EngineerOS.
Provides form fields and validation for student academic details,
career targets, external portfolio links, skills, and interests.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, TextAreaField, SelectField, SubmitField
from wtforms.validators import Optional, Length, NumberRange, URL


class ProfileForm(FlaskForm):
    """Form for editing complete student profile information."""

    # --- Academic Details ---
    college = StringField(
        'College / University Name',
        validators=[Optional(), Length(max=200, message='College name cannot exceed 200 characters.')],
        render_kw={'placeholder': 'e.g. ABC Institute of Technology'}
    )
    branch = StringField(
        'Engineering Branch / Major',
        validators=[Optional(), Length(max=100, message='Branch name cannot exceed 100 characters.')],
        render_kw={'placeholder': 'e.g. Computer Science and Engineering'}
    )
    year = SelectField(
        'Year of Study',
        choices=[
            ('', '-- Select Year --'),
            ('1', '1st Year (Freshman)'),
            ('2', '2nd Year (Sophomore)'),
            ('3', '3rd Year (Junior)'),
            ('4', '4th Year (Senior)')
        ],
        validators=[Optional()]
    )
    semester = SelectField(
        'Current Semester',
        choices=[
            ('', '-- Select Semester --'),
            ('1', 'Semester 1'),
            ('2', 'Semester 2'),
            ('3', 'Semester 3'),
            ('4', 'Semester 4'),
            ('5', 'Semester 5'),
            ('6', 'Semester 6'),
            ('7', 'Semester 7'),
            ('8', 'Semester 8')
        ],
        validators=[Optional()]
    )
    cgpa = DecimalField(
        'Current CGPA (out of 10.0)',
        places=2,
        validators=[
            Optional(),
            NumberRange(min=0.0, max=10.0, message='CGPA must be between 0.0 and 10.0')
        ],
        render_kw={'placeholder': 'e.g. 8.50', 'step': '0.01', 'min': '0.0', 'max': '10.0'}
    )

    # --- Career Goals ---
    target_role = StringField(
        'Target Career Role / Dream Job',
        validators=[Optional(), Length(max=100, message='Target role cannot exceed 100 characters.')],
        render_kw={'placeholder': 'e.g. Full Stack Web Developer, AI/ML Engineer, Cloud Architect'}
    )
    preferred_domain = SelectField(
        'Preferred Tech Domain',
        choices=[
            ('', '-- Select Preferred Domain --'),
            ('Web Development', 'Web Development (Frontend / Full Stack / Backend)'),
            ('Artificial Intelligence & ML', 'Artificial Intelligence, Machine Learning & Data Science'),
            ('Cloud Computing & DevOps', 'Cloud Computing, DevOps & Infrastructure'),
            ('Mobile App Development', 'Mobile App Development (Android / iOS / Flutter)'),
            ('Cybersecurity', 'Cybersecurity & Ethical Hacking'),
            ('Embedded Systems & IoT', 'Embedded Systems, Robotics & IoT'),
            ('Software Engineering / Systems', 'Software Engineering, Algorithms & Systems')
        ],
        validators=[Optional()]
    )
    career_timeline = SelectField(
        'Target Career Readiness Timeline',
        choices=[
            ('', '-- Select Timeline --'),
            ('3 months', '3 Months (Immediate placement / internships)'),
            ('6 months', '6 Months (Next semester target)'),
            ('1 year', '1 Year (Upcoming campus placement season)'),
            ('2+ years', '2+ Years (Long-term engineering preparation)')
        ],
        validators=[Optional()]
    )
    target_companies = TextAreaField(
        'Dream Companies / Organizations',
        validators=[Optional()],
        render_kw={
            'placeholder': 'e.g. Google, Microsoft, Amazon, Infosys, Tech Startups (comma separated)',
            'rows': 2
        }
    )

    # --- External Portfolio & Profiles ---
    github_url = StringField(
        'GitHub Profile URL',
        validators=[Optional(), Length(max=255), URL(require_tld=False, message='Please enter a valid GitHub URL.')],
        render_kw={'placeholder': 'https://github.com/your-username'}
    )
    linkedin_url = StringField(
        'LinkedIn Profile URL',
        validators=[Optional(), Length(max=255), URL(require_tld=False, message='Please enter a valid LinkedIn URL.')],
        render_kw={'placeholder': 'https://linkedin.com/in/your-profile'}
    )
    leetcode_url = StringField(
        'LeetCode / Coding Profile URL',
        validators=[Optional(), Length(max=255), URL(require_tld=False, message='Please enter a valid URL.')],
        render_kw={'placeholder': 'https://leetcode.com/your-username or HackerRank / Codeforces'}
    )

    submit = SubmitField('Save Profile Details')
