"""
Skill model storing user skills and their proficiency levels.
"""
from datetime import datetime, timezone
from app.extensions import db

class Skill(db.Model):
    """
    Represents a specific skill acquired by the user and its proficiency level.
    """
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Enum('beginner', 'intermediate', 'advanced', name='skill_level'), default='beginner')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='uq_user_skill'),
    )

    def __repr__(self):
        return f'<Skill {self.name} ({self.level})>'
