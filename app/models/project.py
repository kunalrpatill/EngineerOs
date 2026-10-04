"""
Project and ProjectTask models.
"""
from datetime import datetime, timezone
from app.extensions import db

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(50)) # Beginner, Intermediate, Advanced
    status = db.Column(db.String(50), default='Not Started') # Not Started, In Progress, Paused, Completed
    
    technologies = db.Column(db.JSON)
    skills = db.Column(db.JSON)
    
    estimated_hours = db.Column(db.Integer, default=0)
    time_spent = db.Column(db.Integer, default=0)
    
    github_url = db.Column(db.String(255))
    live_demo_url = db.Column(db.String(255))
    
    is_ai_recommended = db.Column(db.Boolean, default=False)
    justification = db.Column(db.Text) # Why it was recommended
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    tasks = db.relationship('ProjectTask', backref='project', cascade='all, delete-orphan')

    @property
    def progress_percentage(self):
        if not self.tasks:
            return 0 if self.status != 'Completed' else 100
        completed_tasks = sum(1 for t in self.tasks if t.status == 'completed')
        return int((completed_tasks / len(self.tasks)) * 100)

    def __repr__(self):
        return f'<Project {self.title}>'

class ProjectTask(db.Model):
    __tablename__ = 'project_tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    stage = db.Column(db.String(100)) # e.g., Planning, Development, Testing, Deployment
    
    required_skills = db.Column(db.JSON)
    estimated_hours = db.Column(db.Integer, default=0)
    
    status = db.Column(db.String(50), default='not_started') # not_started, in_progress, completed
    order_index = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ProjectTask {self.title}>'
