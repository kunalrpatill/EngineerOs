"""
Roadmap Blueprint for EngineerOS.

Handles AI-powered skill-gap analysis, personalized career roadmap
generation, storage in the database, and display in the UI.
"""
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill
from app.models.interest import Interest
from app.models.roadmap import Roadmap, RoadmapPhase, Milestone
from app.services.ai_service import get_ai_service

roadmap_bp = Blueprint('roadmap', __name__)


def _collect_profile_data(user):
    """
    Gather all relevant student data into a flat dictionary
    that can be passed to the AI service methods.

    Args:
        user (User): The logged-in user model instance.

    Returns:
        dict: Combined profile, skills, interests, and goals data.
    """
    profile = Profile.query.filter_by(user_id=user.id).first()
    skills = Skill.query.filter_by(user_id=user.id).all()
    interests = Interest.query.filter_by(user_id=user.id).all()

    # Build skill names list and skill-level lookup
    skill_names = [s.name for s in skills]
    skill_levels = {s.name: s.level for s in skills}

    return {
        'name': user.name,
        'email': user.email,
        'college': profile.college if profile else None,
        'branch': profile.branch if profile else None,
        'year': profile.year if profile else None,
        'semester': profile.semester if profile else None,
        'cgpa': str(profile.cgpa) if (profile and profile.cgpa) else None,
        'target_role': profile.target_role if profile else None,
        'preferred_domain': profile.preferred_domain if profile else None,
        'career_timeline': profile.career_timeline if profile else None,
        'target_companies': profile.target_companies if profile else None,
        'github_url': profile.github_url if profile else None,
        'linkedin_url': profile.linkedin_url if profile else None,
        'leetcode_url': profile.leetcode_url if profile else None,
        'skills': skill_names,
        'skill_levels': skill_levels,
        'interests': [i.name for i in interests],
    }


@roadmap_bp.route('/')
@login_required
def index():
    """
    Show the student's active roadmap, or a prompt to generate one.

    If the student already has an active roadmap, display its overview
    with the skill-gap analysis summary. Otherwise, show a "Generate
    Your Roadmap" call-to-action.
    """
    # Find the student's most recent active roadmap
    active_roadmap = Roadmap.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(Roadmap.created_at.desc()).first()

    # Check if the student has the minimum profile for generation
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    skills_count = Skill.query.filter_by(user_id=current_user.id).count()
    has_minimum_profile = (
        profile is not None
        and profile.target_role is not None
        and len(profile.target_role.strip()) > 0
        and skills_count >= 1
    )

    # Parse analysis data for display
    strong_areas = []
    gaps_identified = []
    if active_roadmap:
        if active_roadmap.strong_areas:
            try:
                strong_areas = json.loads(active_roadmap.strong_areas)
            except (json.JSONDecodeError, TypeError):
                strong_areas = [s.strip() for s in active_roadmap.strong_areas.split(',') if s.strip()]
        if active_roadmap.gaps_identified:
            try:
                gaps_identified = json.loads(active_roadmap.gaps_identified)
            except (json.JSONDecodeError, TypeError):
                gaps_identified = [g.strip() for g in active_roadmap.gaps_identified.split(',') if g.strip()]

    return render_template(
        'roadmap/index.html',
        roadmap=active_roadmap,
        has_minimum_profile=has_minimum_profile,
        strong_areas=strong_areas,
        gaps_identified=gaps_identified
    )


@roadmap_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """
    Trigger AI-powered roadmap generation.

    1. Validates the student has a target role and at least 1 skill.
    2. Collects all profile data into a dictionary.
    3. Calls the AI service (Gemini or Mock) to generate a roadmap.
    4. Deactivates any existing active roadmaps for this user.
    5. Stores the new roadmap, phases, and milestones in the database.
    6. Redirects to the roadmap view page.
    """
    # 1. Check minimum profile requirements
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    skills_count = Skill.query.filter_by(user_id=current_user.id).count()

    if not profile or not profile.target_role or not profile.target_role.strip():
        flash('Please set a target career role in your profile before generating a roadmap.', 'warning')
        return redirect(url_for('profile.edit'))

    if skills_count < 1:
        flash('Please add at least one skill to your profile before generating a roadmap.', 'warning')
        return redirect(url_for('profile.edit'))

    try:
        # 2. Collect profile data
        profile_data = _collect_profile_data(current_user)

        # 3. Get AI service and generate roadmap
        ai_service = get_ai_service()
        roadmap_data = ai_service.generate_roadmap(profile_data)

        # 4. Deactivate existing active roadmaps for this user
        Roadmap.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).update({'is_active': False})

        # 5. Extract analysis data
        analysis = roadmap_data.get('skill_gap_analysis', {})
        strong_areas = analysis.get('strong_areas', [])
        gaps_identified = analysis.get('gaps_identified', [])
        overall_readiness = analysis.get('overall_readiness', 0)

        # 6. Create the Roadmap row
        new_roadmap = Roadmap(
            user_id=current_user.id,
            title=roadmap_data.get('title', f"Career Roadmap for {current_user.name}"),
            target_role=roadmap_data.get('target_role', profile.target_role),
            estimated_duration=roadmap_data.get('estimated_duration', '6 months'),
            strong_areas=json.dumps(strong_areas),
            gaps_identified=json.dumps(gaps_identified),
            overall_readiness=overall_readiness,
            is_active=True
        )
        db.session.add(new_roadmap)
        db.session.flush()  # Populate new_roadmap.id

        # 7. Create RoadmapPhase and Milestone rows
        for phase_data in roadmap_data.get('phases', []):
            phase = RoadmapPhase(
                roadmap_id=new_roadmap.id,
                phase_number=phase_data.get('phase_number', 1),
                title=phase_data.get('title', 'Untitled Phase'),
                duration=phase_data.get('duration', ''),
                status='not_started'
            )
            db.session.add(phase)
            db.session.flush()  # Populate phase.id

            for milestone_data in phase_data.get('milestones', []):
                milestone = Milestone(
                    phase_id=phase.id,
                    title=milestone_data.get('title', 'Untitled Milestone'),
                    description=milestone_data.get('description', ''),
                    status='not_started',
                    milestone_type=milestone_data.get('type', 'learning'),
                    resources=milestone_data.get('resources', [])
                )
                db.session.add(milestone)

        # 8. Commit everything
        db.session.commit()

        flash('Your personalized career roadmap has been generated!', 'success')
        return redirect(url_for('roadmap.view', roadmap_id=new_roadmap.id))

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while generating your roadmap: {str(e)}', 'danger')
        return redirect(url_for('roadmap.index'))


@roadmap_bp.route('/<int:roadmap_id>')
@login_required
def view(roadmap_id):
    """
    Display a specific roadmap with its full skill-gap analysis,
    phases, and milestones.

    Only the roadmap owner can view their roadmap.
    """
    roadmap = Roadmap.query.filter_by(
        id=roadmap_id,
        user_id=current_user.id
    ).first()

    if not roadmap:
        flash('Roadmap not found.', 'warning')
        return redirect(url_for('roadmap.index'))

    # Parse stored JSON analysis data for template display
    strong_areas = []
    gaps_identified = []
    recommendations = []

    if roadmap.strong_areas:
        try:
            strong_areas = json.loads(roadmap.strong_areas)
        except (json.JSONDecodeError, TypeError):
            strong_areas = [s.strip() for s in roadmap.strong_areas.split(',') if s.strip()]

    if roadmap.gaps_identified:
        try:
            gaps_identified = json.loads(roadmap.gaps_identified)
        except (json.JSONDecodeError, TypeError):
            gaps_identified = [g.strip() for g in roadmap.gaps_identified.split(',') if g.strip()]

    # Load phases with their milestones (ordered by phase_number)
    phases = RoadmapPhase.query.filter_by(
        roadmap_id=roadmap.id
    ).order_by(RoadmapPhase.phase_number.asc()).all()

    # Calculate progress stats
    total_milestones = 0
    completed_milestones = 0
    for phase in phases:
        for m in phase.milestones:
            total_milestones += 1
            if m.status == 'completed':
                completed_milestones += 1

    progress_pct = int((completed_milestones / total_milestones) * 100) if total_milestones > 0 else 0

    return render_template(
        'roadmap/view.html',
        roadmap=roadmap,
        phases=phases,
        strong_areas=strong_areas,
        gaps_identified=gaps_identified,
        total_milestones=total_milestones,
        completed_milestones=completed_milestones,
        progress_pct=progress_pct
    )
