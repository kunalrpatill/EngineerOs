"""
User model for authentication and basic account details.
"""
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager

class User(UserMixin, db.Model):
    """
    Stores core user credentials and authentication data.
    Implements UserMixin for Flask-Login compatibility.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    skills = db.relationship('Skill', backref='user', cascade='all, delete-orphan')
    interests = db.relationship('Interest', backref='user', cascade='all, delete-orphan')
    roadmaps = db.relationship('Roadmap', backref='user', cascade='all, delete-orphan')
    progress_entries = db.relationship('Progress', backref='user', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hashes the password and sets it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks the given password against the hashed password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(user_id):
    """Callback for Flask-Login to load the user by ID."""
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None

