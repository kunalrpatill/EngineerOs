"""
Career Readiness Engine for EngineerOS.

Calculates a comprehensive, dynamic career readiness score (0-100%)
based on roadmap milestones completed, skill proficiencies, logged
accomplishments (projects/courses), and profile clarity.

Also provides synchronizers for roadmap phase statuses.
"""
from app.extensions import db
from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill
from app.models.roadmap import Roadmap, RoadmapPhase, Milestone
from app.models.progress import Progress


def calculate_readiness(user_id):
    """
    Calculate the dynamic career readiness score (0-100) for a student.

    Scoring Breakdown (100 points total):
    1. Active Roadmap Milestones (up to 40 pts):
       - Ratio of completed milestones over total milestones.
    2. Skills Depth & Proficiency (up to 25 pts):
       - Advanced (5 pts), Intermediate (3 pts), Beginner (1 pt).
    3. Logged Accomplishments (up to 20 pts):
       - Projects (6 pts), Courses (4 pts), Extra skills (2 pts).
    4. Profile & Goal Clarity (up to 15 pts):
       - Target role (5 pts), Domain (3 pts), Portfolio links (4 pts), Academics (3 pts).

    Args:
        user_id (int): The student's user ID.

    Returns:
        int: Readiness percentage between 0 and 100.
    """
    score = 0

    # 1. Active Roadmap Milestones Component (up to 40 points)
    active_roadmap = Roadmap.query.filter_by(user_id=user_id, is_active=True).first()
    if active_roadmap:
        total_milestones = 0
        completed_milestones = 0
        for phase in active_roadmap.phases:
            for m in phase.milestones:
                total_milestones += 1
                if m.status == 'completed':
                    completed_milestones += 1

        if total_milestones > 0:
            score += int((completed_milestones / total_milestones) * 40)

    # 2. Skills Depth & Proficiency (up to 25 points)
    skills = Skill.query.filter_by(user_id=user_id).all()
    skills_score = 0
    for s in skills:
        if s.level == 'advanced':
            skills_score += 5
        elif s.level == 'intermediate':
            skills_score += 3
        else:
            skills_score += 1
    score += min(25, skills_score)

    # 3. Logged Accomplishments (up to 20 points)
    progress_entries = Progress.query.filter_by(user_id=user_id).all()
    accomplishment_score = 0
    for p in progress_entries:
        if p.type == 'project_completed':
            accomplishment_score += 6
        elif p.type == 'course_completed':
            accomplishment_score += 4
        elif p.type == 'skill_added':
            accomplishment_score += 2
    score += min(20, accomplishment_score)

    # 4. Profile & Goal Clarity (up to 15 points)
    profile = Profile.query.filter_by(user_id=user_id).first()
    if profile:
        if profile.target_role and profile.target_role.strip():
            score += 5
        if profile.preferred_domain and profile.preferred_domain.strip():
            score += 3
        if (profile.github_url and profile.github_url.strip()) or \
           (profile.linkedin_url and profile.linkedin_url.strip()) or \
           (profile.leetcode_url and profile.leetcode_url.strip()):
            score += 4
        if profile.college and profile.college.strip() and profile.cgpa:
            score += 3

    return min(100, max(0, score))


def sync_roadmap_and_phase_status(roadmap_id):
    """
    Synchronize phase status (not_started, in_progress, completed)
    and overall roadmap readiness for a given roadmap.

    Args:
        roadmap_id (int): ID of the roadmap to synchronize.
    """
    roadmap = db.session.get(Roadmap, roadmap_id)
    if not roadmap:
        return


    for phase in roadmap.phases:
        milestones = phase.milestones
        if not milestones:
            continue

        total_m = len(milestones)
        completed_m = len([m for m in milestones if m.status == 'completed'])

        if completed_m == total_m:
            phase.status = 'completed'
        elif completed_m > 0:
            phase.status = 'in_progress'
        else:
            phase.status = 'not_started'

    # Update roadmap's stored overall readiness score
    roadmap.overall_readiness = calculate_readiness(roadmap.user_id)
