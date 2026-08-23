"""
Roadmap, RoadmapPhase, and Milestone models for career tracks.
"""
from datetime import datetime, timezone
from app.extensions import db

class Roadmap(db.Model):
    """
    Stores generated roadmaps for users, representing an entire career learning track.
    """
    __tablename__ = 'roadmaps'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    target_role = db.Column(db.String(100))
    estimated_duration = db.Column(db.String(50))
    strong_areas = db.Column(db.Text)
    gaps_identified = db.Column(db.Text)
    overall_readiness = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    phases = db.relationship('RoadmapPhase', backref='roadmap', cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_user_active', 'user_id', 'is_active'),
    )

    def __repr__(self):
        return f'<Roadmap {self.title}>'


class RoadmapPhase(db.Model):
    """
    Represents a specific phase within a generated roadmap.
    """
    __tablename__ = 'roadmap_phases'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    roadmap_id = db.Column(db.Integer, db.ForeignKey('roadmaps.id', ondelete='CASCADE'), nullable=False)
    phase_number = db.Column(db.SmallInteger, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    duration = db.Column(db.String(50))
    status = db.Column(db.Enum('not_started', 'in_progress', 'completed', name='phase_status'), default='not_started')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    milestones = db.relationship('Milestone', backref='phase', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('roadmap_id', 'phase_number', name='uq_roadmap_phase'),
    )

    def __repr__(self):
        return f'<RoadmapPhase {self.title}>'


class Milestone(db.Model):
    """
    Represents a specific task or learning objective within a roadmap phase.
    """
    __tablename__ = 'milestones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phase_id = db.Column(db.Integer, db.ForeignKey('roadmap_phases.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum('not_started', 'in_progress', 'completed', name='milestone_status'), default='not_started')
    milestone_type = db.Column(db.Enum('learning', 'project', 'practice', 'assessment', name='milestone_type'), default='learning')
    resources = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Milestone {self.title}>'

