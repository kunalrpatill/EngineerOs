"""
Profile Blueprint for EngineerOS.
Handles viewing and updating student academic info, career goals, skills, and interests.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.profile import Profile
from app.models.skill import Skill
from app.models.interest import Interest
from app.forms.profile_forms import ProfileForm
from app.utils.completion import calculate_profile_completion

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/')
@login_required
def view():
    """
    Display the student's complete profile, including academics,
    career goals, skills breakdown, interests, and profile readiness score.
    """
    # 1. Fetch or create user profile
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id, completion_percentage=0)
        db.session.add(profile)
        db.session.commit()

    # 2. Fetch associated skills and interests
    skills = Skill.query.filter_by(user_id=current_user.id).order_by(Skill.name.asc()).all()
    interests = Interest.query.filter_by(user_id=current_user.id).order_by(Interest.name.asc()).all()

    # 3. Calculate and sync completion percentage
    completion = calculate_profile_completion(profile, skills, interests)
    if profile.completion_percentage != completion:
        profile.completion_percentage = completion
        db.session.commit()

    # 4. Parse comma-separated target companies into a clean list
    companies_list = []
    if profile.target_companies:
        companies_list = [c.strip() for c in profile.target_companies.split(',') if c.strip()]

    # 5. Group skills by proficiency level for clear display
    grouped_skills = {
        'advanced': [s for s in skills if s.level == 'advanced'],
        'intermediate': [s for s in skills if s.level == 'intermediate'],
        'beginner': [s for s in skills if s.level == 'beginner']
    }

    return render_template(
        'profile/view.html',
        profile=profile,
        skills=skills,
        grouped_skills=grouped_skills,
        interests=interests,
        companies_list=companies_list,
        completion=completion
    )


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """
    Render profile editor and process updates for academic details,
    goals, dynamic skills, and interests.
    """
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id, completion_percentage=0)
        db.session.add(profile)
        db.session.commit()

    form = ProfileForm()

    if request.method == 'GET':
        # Populate form fields with existing profile values
        form.college.data = profile.college
        form.branch.data = profile.branch
        form.year.data = str(profile.year) if profile.year else ''
        form.semester.data = str(profile.semester) if profile.semester else ''
        form.cgpa.data = profile.cgpa
        form.target_role.data = profile.target_role
        form.preferred_domain.data = profile.preferred_domain
        form.career_timeline.data = profile.career_timeline
        form.target_companies.data = profile.target_companies
        form.github_url.data = profile.github_url
        form.linkedin_url.data = profile.linkedin_url
        form.leetcode_url.data = profile.leetcode_url

    if form.validate_on_submit():
        try:
            # 1. Update basic profile attributes
            profile.college = form.college.data.strip() if form.college.data else None
            profile.branch = form.branch.data.strip() if form.branch.data else None
            profile.year = int(form.year.data) if form.year.data else None
            profile.semester = int(form.semester.data) if form.semester.data else None
            profile.cgpa = form.cgpa.data if form.cgpa.data is not None else None
            profile.target_role = form.target_role.data.strip() if form.target_role.data else None
            profile.preferred_domain = form.preferred_domain.data if form.preferred_domain.data else None
            profile.career_timeline = form.career_timeline.data if form.career_timeline.data else None
            profile.target_companies = form.target_companies.data.strip() if form.target_companies.data else None
            profile.github_url = form.github_url.data.strip() if form.github_url.data else None
            profile.linkedin_url = form.linkedin_url.data.strip() if form.linkedin_url.data else None
            profile.leetcode_url = form.leetcode_url.data.strip() if form.leetcode_url.data else None

            # 2. Update dynamic skills list
            skill_names = request.form.getlist('skill_names[]') or request.form.getlist('skill_names')
            skill_levels = request.form.getlist('skill_levels[]') or request.form.getlist('skill_levels')

            # Delete old skills and add new validated skills
            Skill.query.filter_by(user_id=current_user.id).delete()
            seen_skills = set()
            for name, level in zip(skill_names, skill_levels):
                clean_name = name.strip()
                if clean_name and clean_name.lower() not in seen_skills:
                    seen_skills.add(clean_name.lower())
                    valid_level = level if level in ['beginner', 'intermediate', 'advanced'] else 'beginner'
                    db.session.add(Skill(user_id=current_user.id, name=clean_name, level=valid_level))

            # 3. Update dynamic interests list
            interest_names = request.form.getlist('interest_names[]') or request.form.getlist('interest_names')
            # Also handle comma-separated fallback input if provided
            extra_interests = request.form.get('extra_interests', '')
            if extra_interests:
                interest_names.extend(extra_interests.split(','))

            Interest.query.filter_by(user_id=current_user.id).delete()
            seen_interests = set()
            for item in interest_names:
                clean_item = item.strip()
                if clean_item and clean_item.lower() not in seen_interests:
                    seen_interests.add(clean_item.lower())
                    db.session.add(Interest(user_id=current_user.id, name=clean_item))

            db.session.flush()

            # 4. Calculate updated completion percentage
            updated_skills = Skill.query.filter_by(user_id=current_user.id).all()
            updated_interests = Interest.query.filter_by(user_id=current_user.id).all()
            profile.completion_percentage = calculate_profile_completion(profile, updated_skills, updated_interests)

            db.session.commit()
            flash('Your profile has been saved successfully!', 'success')
            return redirect(url_for('profile.view'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while saving your profile: {str(e)}', 'danger')

    # For rendering edit template with existing skills & interests
    existing_skills = Skill.query.filter_by(user_id=current_user.id).order_by(Skill.id.asc()).all()
    existing_interests = Interest.query.filter_by(user_id=current_user.id).order_by(Interest.id.asc()).all()

    return render_template(
        'profile/edit.html',
        form=form,
        profile=profile,
        existing_skills=existing_skills,
        existing_interests=existing_interests
    )
