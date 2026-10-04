from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Project, ProjectTask
from app.services.ai_service import get_ai_service
import json

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/', methods=['GET'])
@login_required
def index():
    # Gather projects for user
    all_projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.updated_at.desc()).all()
    
    active_projects = [p for p in all_projects if p.status == 'In Progress']
    completed_projects = [p for p in all_projects if p.status == 'Completed']
    
    total_progress = sum(p.progress_percentage for p in active_projects)
    avg_progress = (total_progress / len(active_projects)) if active_projects else 0
    
    # Skills practiced
    skills_practiced = set()
    for p in all_projects:
        if p.skills:
            if isinstance(p.skills, list):
                skills_practiced.update(p.skills)
            elif isinstance(p.skills, str):
                try:
                    s_list = json.loads(p.skills)
                    skills_practiced.update(s_list)
                except:
                    pass

    return render_template('projects/index.html', 
                           projects=all_projects,
                           active_projects=active_projects,
                           completed_projects=completed_projects,
                           avg_progress=int(avg_progress),
                           skills_practiced=len(skills_practiced))

@projects_bp.route('/recommendations', methods=['POST'])
@login_required
def recommendations():
    profile = current_user.profile
    if not profile:
        return jsonify({"error": "Profile not found"}), 400
        
    profile_data = {
        'target_role': profile.target_role,
        'skills': [s.name for s in current_user.skills]
    }
    
    ai = get_ai_service()
    recs = ai.generate_project_recommendations(profile_data)
    
    return jsonify({"recommendations": recs})

@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        difficulty = request.form.get('difficulty')
        estimated_hours = request.form.get('estimated_time', 0)
        
        techs = request.form.get('technologies', '')
        skills = request.form.get('skills', '')
        
        technologies_list = [t.strip() for t in techs.split(',') if t.strip()]
        skills_list = [s.strip() for s in skills.split(',') if s.strip()]
        
        is_ai_recommended = request.form.get('is_ai_recommended', 'false').lower() == 'true'
        justification = request.form.get('justification', '')
        
        project = Project(
            user_id=current_user.id,
            title=title,
            description=description,
            difficulty=difficulty,
            estimated_hours=int(estimated_hours) if str(estimated_hours).isdigit() else 20,
            technologies=technologies_list,
            skills=skills_list,
            is_ai_recommended=is_ai_recommended,
            justification=justification,
            status='Not Started'
        )
        
        db.session.add(project)
        db.session.commit()
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('projects.view', project_id=project.id))
        
    return render_template('projects/create.html')

@projects_bp.route('/<int:project_id>', methods=['GET'])
@login_required
def view(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('projects.index'))
        
    return render_template('projects/view.html', project=project)

@projects_bp.route('/<int:project_id>/roadmap', methods=['POST'])
@login_required
def generate_roadmap(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    if project.tasks:
        return jsonify({"message": "Roadmap already generated"}), 200
        
    profile = current_user.profile
    profile_data = {
        'target_role': profile.target_role if profile else 'Software Engineer',
        'skills': [s.name for s in current_user.skills]
    }
    
    project_data = {
        'title': project.title,
        'description': project.description,
        'technologies': project.technologies or []
    }
    
    ai = get_ai_service()
    roadmap_data = ai.generate_project_roadmap(project_data, profile_data)
    
    order = 0
    for stage_data in roadmap_data:
        stage = stage_data.get('stage', 'Development')
        for task_data in stage_data.get('tasks', []):
            task = ProjectTask(
                project_id=project.id,
                title=task_data.get('title'),
                description=task_data.get('description'),
                stage=stage,
                required_skills=task_data.get('required_skills', []),
                estimated_hours=task_data.get('estimated_hours', 2),
                order_index=order
            )
            db.session.add(task)
            order += 1
            
    project.status = 'In Progress'
    db.session.commit()
    
    flash('Project roadmap generated successfully!', 'success')
    return jsonify({"success": True, "redirect": url_for('projects.view', project_id=project.id)})

@projects_bp.route('/<int:project_id>/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(project_id, task_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    task = ProjectTask.query.get_or_404(task_id)
    if task.project_id != project.id:
        return jsonify({"error": "Bad request"}), 400
        
    data = request.get_json()
    completed = data.get('completed', False)
    
    task.status = 'completed' if completed else 'not_started'
    
    # Check if all tasks are completed
    all_completed = all(t.status == 'completed' for t in project.tasks)
    if all_completed and project.tasks:
        if project.status != 'Completed':
            project.status = 'Completed'
            # Skill Mapping integration
            from app.models.skill import Skill
            for p_skill in (project.skills or []):
                existing_skill = Skill.query.filter_by(user_id=current_user.id, name=p_skill).first()
                if existing_skill:
                    # Bump skill level
                    if existing_skill.level == 'beginner':
                        existing_skill.level = 'intermediate'
                    elif existing_skill.level == 'intermediate':
                        existing_skill.level = 'advanced'
                else:
                    new_skill = Skill(user_id=current_user.id, name=p_skill, level='beginner')
                    db.session.add(new_skill)
            
            from app.models.progress import Progress
            prog = Progress(
                user_id=current_user.id,
                type='project_completed',
                title=f'Completed Project: {project.title}',
                description=project.description,
                skills_gained=','.join(project.skills or [])
            )
            db.session.add(prog)
    elif project.status == 'Completed' and not all_completed:
        project.status = 'In Progress'
        
    db.session.commit()
    
    return jsonify({
        "success": True, 
        "project_status": project.status, 
        "progress": project.progress_percentage
    })

@projects_bp.route('/<int:project_id>/assistant', methods=['POST'])
@login_required
def assistant(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json()
    question = data.get('question')
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
        
    project_context = {
        'title': project.title,
        'stage': project.status,
        'technologies': project.technologies or []
    }
    
    ai = get_ai_service()
    result = ai.project_assistant(question, project_context)
    
    return jsonify(result)
    
@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('projects.index'))
        
    db.session.delete(project)
    db.session.commit()
    
    flash('Project deleted.', 'info')
    return redirect(url_for('projects.index'))

@projects_bp.route('/<int:project_id>/edit', methods=['POST'])
@login_required
def edit(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    github_url = request.form.get('github_url')
    live_demo_url = request.form.get('live_demo_url')
    
    if github_url is not None:
        project.github_url = github_url
    if live_demo_url is not None:
        project.live_demo_url = live_demo_url
        
    db.session.commit()
    flash('Project links updated.', 'success')
    return redirect(url_for('projects.view', project_id=project.id))
