"""
Interest model storing user interests.
"""
from datetime import datetime, timezone
from app.extensions import db

class Interest(db.Model):
    """
    Represents specific technical or career interests associated with a user.
    """
    __tablename__ = 'interests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='uq_user_interest'),
    )

    def __repr__(self):
        return f'<Interest {self.name}>'
