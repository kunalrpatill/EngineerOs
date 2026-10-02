from app.extensions import db
from datetime import datetime

class PracticeQuestion(db.Model):
    __tablename__ = 'practice_questions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    subtopic = db.Column(db.String(100), nullable=True)
    difficulty = db.Column(db.String(20), nullable=False) # Easy, Medium, Hard
    question_type = db.Column(db.String(50), nullable=False) # MCQ, Output Prediction, Debugging, Conceptual, Coding Problem
    
    # Specific fields for MCQ and similar
    options = db.Column(db.JSON, nullable=True) # list of options
    correct_answer = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    
    # Specific fields for Coding Problems
    starter_code = db.Column(db.Text, nullable=True)
    input_format = db.Column(db.Text, nullable=True)
    output_format = db.Column(db.Text, nullable=True)
    constraints = db.Column(db.Text, nullable=True)
    sample_input = db.Column(db.Text, nullable=True)
    sample_output = db.Column(db.Text, nullable=True)
    
    verified = db.Column(db.Boolean, default=False, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to attempts
    attempts = db.relationship('PracticeAttempt', backref='question_ref', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PracticeQuestion {self.id}: {self.title}>"

class PracticeAttempt(db.Model):
    __tablename__ = 'practice_attempts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('practice_questions.id'), nullable=False)
    
    submitted_answer = db.Column(db.Text, nullable=True)
    result = db.Column(db.Boolean, nullable=False) # True if correct, False otherwise
    attempt_count = db.Column(db.Integer, default=1, nullable=False)
    completed_status = db.Column(db.Boolean, default=False, nullable=False)
    submitted_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('practice_attempts', lazy=True))

    def __repr__(self):
        return f"<PracticeAttempt User:{self.user_id} Question:{self.question_id} Result:{self.result}>"
