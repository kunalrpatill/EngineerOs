"""
Progress Blueprint for EngineerOS.

Handles tracking student career readiness, roadmap milestone completions,
manual accomplishment logging (projects, courses, certifications),
and the interactive activity timeline feed.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.roadmap import Roadmap, RoadmapPhase, Milestone
from app.models.progress import Progress
from app.models.skill import Skill
from app.forms.progress_forms import AccomplishmentForm
from app.services.readiness import calculate_readiness, sync_roadmap_and_phase_status

progress_bp = Blueprint('progress', __name__)


@progress_bp.route('/')
@login_required
def index():
    """
    Display student progress overview, live career readiness gauge,
    roadmap milestone summary, and filterable accomplishment feed.
    """
    # 1. Calculate live dynamic career readiness score
    readiness = calculate_readiness(current_user.id)

    # 2. Fetch active roadmap and milestone statistics
    active_roadmap = Roadmap.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(Roadmap.created_at.desc()).first()

    total_milestones = 0
    completed_milestones = 0
    if active_roadmap:
        for phase in active_roadmap.phases:
            for m in phase.milestones:
                total_milestones += 1
                if m.status == 'completed':
                    completed_milestones += 1

    milestones_pct = int((completed_milestones / total_milestones) * 100) if total_milestones > 0 else 0

    # 3. Fetch progress entries with optional type filter
    filter_type = request.args.get('type', 'all')
    query = Progress.query.filter_by(user_id=current_user.id)
    if filter_type in ['milestone_completed', 'project_completed', 'course_completed', 'skill_added']:
        query = query.filter_by(type=filter_type)

    progress_entries = query.order_by(Progress.created_at.desc(), Progress.id.desc()).all()

    # 4. Total counts for summary stats
    all_entries = Progress.query.filter_by(user_id=current_user.id).all()
    projects_count = len([p for p in all_entries if p.type == 'project_completed'])
    courses_count = len([p for p in all_entries if p.type == 'course_completed'])
    skills_count = Skill.query.filter_by(user_id=current_user.id).count()

    form = AccomplishmentForm()

    return render_template(
        'progress/index.html',
        readiness=readiness,
        active_roadmap=active_roadmap,
        total_milestones=total_milestones,
        completed_milestones=completed_milestones,
        milestones_pct=milestones_pct,
        progress_entries=progress_entries,
        filter_type=filter_type,
        projects_count=projects_count,
        courses_count=courses_count,
        skills_count=skills_count,
        form=form
    )


@progress_bp.route('/milestone/<int:milestone_id>/toggle', methods=['POST'])
@login_required
def toggle_milestone(milestone_id):
    """
    Toggle milestone completion status (completed <-> not_started).
    Automatically updates phase status, records or removes Progress entry,
    and recalculates career readiness.
    """
    milestone = db.session.get(Milestone, milestone_id)
    if not milestone:
        flash('Milestone not found.', 'warning')
        return redirect(url_for('progress.index'))


    # Verify authorization: student must own the roadmap this milestone belongs to
    if milestone.phase.roadmap.user_id != current_user.id:
        flash('Unauthorized access to milestone.', 'danger')
        return redirect(url_for('progress.index'))

    readiness_before = calculate_readiness(current_user.id)
    roadmap_id = milestone.phase.roadmap_id

    if milestone.status == 'completed':
        # Revert milestone to not_started
        milestone.status = 'not_started'
        # Remove the progress record for this milestone
        Progress.query.filter_by(user_id=current_user.id, milestone_id=milestone.id).delete()
        sync_roadmap_and_phase_status(roadmap_id)
        db.session.commit()
        flash(f'Milestone "{milestone.title}" reverted to pending.', 'info')
    else:
        # Mark milestone as completed
        milestone.status = 'completed'
        sync_roadmap_and_phase_status(roadmap_id)
        readiness_after = calculate_readiness(current_user.id)

        # Create progress record
        progress_entry = Progress(
            user_id=current_user.id,
            roadmap_id=roadmap_id,
            milestone_id=milestone.id,
            type='milestone_completed',
            title=f'Completed: {milestone.title}',
            description=milestone.description,
            readiness_before=readiness_before,
            readiness_after=readiness_after
        )
        db.session.add(progress_entry)
        db.session.commit()
        flash(f'Milestone "{milestone.title}" marked as completed!', 'success')

    # Return to the referring page (e.g. roadmap view or progress dashboard)
    next_url = request.referrer or url_for('roadmap.view', roadmap_id=roadmap_id)
    return redirect(next_url)


@progress_bp.route('/log', methods=['POST'])
@login_required
def log_accomplishment():
    """
    Log a student accomplishment (project, course, or certification).
    Calculates readiness delta and commits to progress feed.
    """
    form = AccomplishmentForm()
    if form.validate_on_submit():
        try:
            readiness_before = calculate_readiness(current_user.id)
            active_roadmap = Roadmap.query.filter_by(user_id=current_user.id, is_active=True).first()

            entry = Progress(
                user_id=current_user.id,
                roadmap_id=active_roadmap.id if active_roadmap else None,
                type=form.type.data,
                title=form.title.data.strip(),
                description=form.description.data.strip() if form.description.data else None,
                skills_gained=form.skills_gained.data.strip() if form.skills_gained.data else None,
                readiness_before=readiness_before
            )
            db.session.add(entry)
            db.session.flush()

            # Recalculate readiness with new accomplishment included
            readiness_after = calculate_readiness(current_user.id)
            entry.readiness_after = readiness_after

            if active_roadmap:
                active_roadmap.overall_readiness = readiness_after

            db.session.commit()
            flash('Accomplishment logged successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error logging accomplishment: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('progress.index'))


@progress_bp.route('/delete/<int:progress_id>', methods=['POST'])
@login_required
def delete_accomplishment(progress_id):
    """
    Delete a logged accomplishment entry.
    Ensures ownership and updates readiness.
    """
    entry = Progress.query.filter_by(id=progress_id, user_id=current_user.id).first()
    if not entry:
        flash('Accomplishment not found or access denied.', 'warning')
        return redirect(url_for('progress.index'))

    # If this was a milestone completion, revert the milestone status too
    if entry.milestone_id:
        milestone = db.session.get(Milestone, entry.milestone_id)
        if milestone and milestone.phase.roadmap.user_id == current_user.id:
            milestone.status = 'not_started'
            sync_roadmap_and_phase_status(milestone.phase.roadmap_id)


    db.session.delete(entry)
    active_roadmap = Roadmap.query.filter_by(user_id=current_user.id, is_active=True).first()
    if active_roadmap:
        active_roadmap.overall_readiness = calculate_readiness(current_user.id)

    db.session.commit()
    flash('Accomplishment entry removed.', 'info')
    return redirect(url_for('progress.index'))
