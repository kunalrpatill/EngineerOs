"""
Dashboard Blueprint for EngineerOS.
Provides the central hub for student metrics, career readiness, and quick actions.
"""
import json
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.profile import Profile
from app.models.skill import Skill
from app.models.interest import Interest
from app.models.roadmap import Roadmap, RoadmapPhase, Milestone
from app.models.progress import Progress
from app.utils.completion import calculate_profile_completion
from app.services.readiness import calculate_readiness

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """
    Render the comprehensive career-readiness dashboard.

    Aggregates data from all phases:
    - Phase 2: Profile, skills, interests, profile completion
    - Phase 3: Active roadmap, skill-gap analysis (strong areas & gaps)
    - Phase 4: Career readiness score, milestone stats, recent progress entries
    """
    # ── Phase 2 Data (existing) ──────────────────────────────────────────
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    skills = Skill.query.filter_by(user_id=current_user.id).all()
    interests = Interest.query.filter_by(user_id=current_user.id).all()
    completion = calculate_profile_completion(profile, skills, interests)

    # ── Phase 3 Data: Active Roadmap & Skill-Gap Analysis ────────────────
    active_roadmap = Roadmap.query.filter_by(
        user_id=current_user.id, is_active=True
    ).first()

    total_milestones = 0
    completed_milestones = 0
    strong_areas = []
    gaps_identified = []

    if active_roadmap:
        # Count milestones across all phases
        for phase in active_roadmap.phases:
            for m in phase.milestones:
                total_milestones += 1
                if m.status == 'completed':
                    completed_milestones += 1

        # Parse skill-gap data (same pattern as roadmap routes)
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

    milestones_pct = int((completed_milestones / total_milestones) * 100) if total_milestones > 0 else 0

    # ── Phase 4 Data: Readiness Score & Recent Activity ──────────────────
    readiness = calculate_readiness(current_user.id)

    recent_activities = Progress.query.filter_by(
        user_id=current_user.id
    ).order_by(Progress.created_at.desc()).limit(5).all()

    projects_count = Progress.query.filter_by(
        user_id=current_user.id, type='project_completed'
    ).count()

    courses_count = Progress.query.filter_by(
        user_id=current_user.id, type='course_completed'
    ).count()

    return render_template(
        'dashboard/index.html',
        # Phase 2 (unchanged)
        profile=profile,
        skills_count=len(skills),
        interests_count=len(interests),
        completion=completion,
        # Phase 3 (new)
        active_roadmap=active_roadmap,
        strong_areas=strong_areas,
        gaps_identified=gaps_identified,
        # Phase 4 (new)
        readiness=readiness,
        total_milestones=total_milestones,
        completed_milestones=completed_milestones,
        milestones_pct=milestones_pct,
        recent_activities=recent_activities,
        projects_count=projects_count,
        courses_count=courses_count
    )
