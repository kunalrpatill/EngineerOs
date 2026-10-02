from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models.practice import PracticeQuestion, PracticeAttempt
from app.models.roadmap import Roadmap, RoadmapPhase, Milestone
import json

practice_bp = Blueprint('practice', __name__)

@practice_bp.route('/')
@login_required
def index():
    """Main dashboard for Practice Arena."""
    # Get user's roadmap
    roadmap = Roadmap.query.filter_by(user_id=current_user.id, is_active=True).first()
    
    current_topic = None
    recommended_questions = []
    
    if roadmap:
        # Find current in-progress milestone
        current_milestone = Milestone.query.join(RoadmapPhase).filter(
            RoadmapPhase.roadmap_id == roadmap.id,
            Milestone.status == 'in_progress'
        ).first()
        
        # If no in-progress, find first not_started
        if not current_milestone:
             current_milestone = Milestone.query.join(RoadmapPhase).filter(
                 RoadmapPhase.roadmap_id == roadmap.id,
                 Milestone.status == 'not_started'
             ).order_by(RoadmapPhase.phase_number, Milestone.id).first()
             
        if current_milestone:
             current_topic = current_milestone.title
             
             # Fetch verified recommended questions matching topic
             recommended_questions = PracticeQuestion.query.filter_by(
                 verified=True, active=True, topic=current_topic
             ).all()
             
             # If exact match has no questions, try matching language/field broadly or just return all verified
             if not recommended_questions:
                 # Fallback: maybe language match? e.g. "Java"
                 pass
                 
    # Let's get all verified questions for filtering
    all_questions = PracticeQuestion.query.filter_by(verified=True, active=True).all()
    
    # Calculate progress for current_topic if exists
    progress_percent = 0
    completed_count = 0
    total_topic_questions = len(recommended_questions)
    
    if current_topic and total_topic_questions > 0:
        completed_attempts = PracticeAttempt.query.filter_by(
            user_id=current_user.id, completed_status=True
        ).join(PracticeQuestion).filter(
            PracticeQuestion.topic == current_topic
        ).all()
        # Count unique questions completed
        completed_q_ids = set(a.question_id for a in completed_attempts)
        completed_count = len(completed_q_ids)
        progress_percent = int((completed_count / total_topic_questions) * 100)
    
    # Get attempt data to mark completed/not completed
    user_attempts = PracticeAttempt.query.filter_by(user_id=current_user.id).all()
    completed_ids = set(a.question_id for a in user_attempts if a.completed_status)
    attempted_ids = set(a.question_id for a in user_attempts)

    return render_template(
        'practice/index.html',
        roadmap=roadmap,
        current_topic=current_topic,
        recommended_questions=recommended_questions,
        all_questions=all_questions,
        progress_percent=progress_percent,
        completed_count=completed_count,
        total_topic_questions=total_topic_questions,
        completed_ids=completed_ids,
        attempted_ids=attempted_ids
    )

@practice_bp.route('/question/<int:question_id>')
@login_required
def question_detail(question_id):
    """Shows the question details and allows submission."""
    question = PracticeQuestion.query.get_or_404(question_id)
    
    # Check if user already completed it
    attempt = PracticeAttempt.query.filter_by(
        user_id=current_user.id, question_id=question_id, completed_status=True
    ).first()
    
    return render_template('practice/question.html', question=question, already_completed=bool(attempt))

@practice_bp.route('/submit/<int:question_id>', methods=['POST'])
@login_required
def submit_answer(question_id):
    """Handles question submission."""
    question = PracticeQuestion.query.get_or_404(question_id)
    submitted_answer = request.form.get('answer', '')
    
    is_correct = False
    if question.question_type == 'MCQ':
        is_correct = (submitted_answer == question.correct_answer)
    elif question.question_type == 'Output Prediction':
        is_correct = (submitted_answer.strip() == question.correct_answer.strip())
    elif question.question_type == 'Conceptual':
        # For conceptual, maybe it's just self-check or simple keyword match.
        # Let's do exact match for now, or consider it always correct if they attempted it.
        # But for an automated system, usually it's MCQ or simple output.
        is_correct = True # placeholder
    elif question.question_type == 'Debugging':
         is_correct = (submitted_answer.strip() == question.correct_answer.strip())
    
    # Record attempt
    attempt = PracticeAttempt.query.filter_by(
        user_id=current_user.id, question_id=question_id
    ).first()
    
    if not attempt:
        attempt = PracticeAttempt(
            user_id=current_user.id,
            question_id=question_id,
            submitted_answer=submitted_answer,
            result=is_correct,
            completed_status=is_correct,
            attempt_count=1
        )
        db.session.add(attempt)
    else:
        attempt.submitted_answer = submitted_answer
        attempt.result = is_correct
        attempt.attempt_count += 1
        if is_correct:
            attempt.completed_status = True
            
    db.session.commit()
    
    # Flash result
    if is_correct:
        flash('Correct Answer! Well done.', 'success')
    else:
        flash('Incorrect Answer. Try again!', 'danger')
        
    # Set result in session or render directly
    return render_template(
        'practice/result.html', 
        question=question, 
        is_correct=is_correct, 
        submitted_answer=submitted_answer
    )

