"""
Profile model for detailed student profiles.
"""
from datetime import datetime, timezone
from app.extensions import db

class Profile(db.Model):
    """
    Stores detailed profile information for users, including college details,
    career goals, and external links.
    """
    __tablename__ = 'profiles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    college = db.Column(db.String(200))
    branch = db.Column(db.String(100))
    year = db.Column(db.SmallInteger)
    semester = db.Column(db.SmallInteger)
    cgpa = db.Column(db.Numeric(4, 2))
    target_role = db.Column(db.String(100))
    target_companies = db.Column(db.Text)
    preferred_domain = db.Column(db.String(100))
    career_timeline = db.Column(db.String(50))
    github_url = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(255))
    leetcode_url = db.Column(db.String(255))
    completion_percentage = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


    def __repr__(self):
        return f'<Profile User={self.user_id}>'
