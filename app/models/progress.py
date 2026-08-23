"""
Progress model tracking user accomplishments over time.
"""
from datetime import datetime, timezone
from app.extensions import db

class Progress(db.Model):
    """
    Records specific accomplishments and tracks progress events over time.
    """
    __tablename__ = 'progress'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    roadmap_id = db.Column(db.Integer, db.ForeignKey('roadmaps.id', ondelete='SET NULL'))
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id', ondelete='SET NULL'))
    type = db.Column(db.Enum('milestone_completed', 'skill_added', 'project_completed', 'course_completed', name='progress_type'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    skills_gained = db.Column(db.Text)
    readiness_before = db.Column(db.Integer)
    readiness_after = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


    __table_args__ = (
        db.Index('idx_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f'<Progress {self.title}>'
