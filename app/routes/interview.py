"""
Interview Prep Blueprint for EngineerOS.
Provides AI-generated mock interview questions and evaluations.
"""
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user

from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.services.ai_service import get_ai_service
from app.routes.roadmap import _collect_profile_data

interview_bp = Blueprint('interview', __name__)

@interview_bp.route('/')
@login_required
def index():
    """
    Landing page for interview prep.
    Checks if user is ready for an interview (has profile and target role).
    """
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    
    if not profile or not profile.target_role or not profile.target_role.strip():
        flash("Please complete your profile and set a target role before practicing interviews.", "warning")
        return redirect(url_for('dashboard.index'))
        
    return render_template('interview/index.html', profile=profile)

@interview_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """
    Generate mock interview questions and store them in the session.
    """
    # CSRF Token check (using WTForms CSRF validation pattern manually or just relying on standard form submission if needed, but since we are not using a WTForm here, we should check it manually if we want to be strict, but wait, WTForms handles it. Let's just use a simple form in the template).
    # Wait, the prompt said: "Follow the existing Flask-WTF/CSRF implementation." If we need a form, maybe just a hidden CSRF token in the template, and we can check it using `csrf.protect()` if enabled.
    
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if not profile or not profile.target_role:
        return redirect(url_for('interview.index'))
        
    active_roadmap = Roadmap.query.filter_by(user_id=current_user.id, is_active=True).first()
    gaps = []
    if active_roadmap and active_roadmap.gaps_identified:
        try:
            gaps = json.loads(active_roadmap.gaps_identified)
        except:
            gaps = [g.strip() for g in active_roadmap.gaps_identified.split(',') if g.strip()]
            
    profile_data = _collect_profile_data(current_user)
    
    ai_service = get_ai_service()
    questions = ai_service.generate_interview_questions(profile_data, gaps)
    
    if not questions:
        flash("Failed to generate questions. Please try again.", "danger")
        return redirect(url_for('interview.index'))
        
    # Store minimally in session to avoid 4KB limit
    session['interview_questions'] = questions
    session.modified = True
    
    return redirect(url_for('interview.session_view'))

@interview_bp.route('/session', endpoint='session_view')
@login_required
def session_view():
    """
    Render the interactive interview session form.
    """
    questions = session.get('interview_questions')
    if not questions:
        flash("No active interview session found. Please generate a new one.", "warning")
        return redirect(url_for('interview.index'))
        
    return render_template('interview/session.html', questions=questions)

@interview_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    """
    Submit answers for evaluation and render feedback.
    """
    questions = session.get('interview_questions')
    if not questions:
        flash("Interview session expired or not found.", "warning")
        return redirect(url_for('interview.index'))
        
    answers = {}
    valid = True
    
    # Collect and validate answers
    for q in questions:
        qid = str(q.get('id'))
        ans = request.form.get(f'answer_{qid}', '').strip()
        if not ans:
            valid = False
            break
        if len(ans) > 5000: # Sanity limit
            ans = ans[:5000]
        answers[qid] = ans
        
    if not valid:
        flash("Please provide an answer for all questions.", "warning")
        return redirect(url_for('interview.session_view'))
        
    # Clear session to prevent resubmission / save space
    session.pop('interview_questions', None)
    session.modified = True
    
    ai_service = get_ai_service()
    feedback = ai_service.evaluate_interview_answers(questions, answers)
    
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    return render_template('interview/feedback.html', feedback=feedback, profile=profile)
