def register_blueprints(app):
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.profile import profile_bp
    from app.routes.roadmap import roadmap_bp
    from app.routes.progress import progress_bp
    from app.routes.interview import interview_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(roadmap_bp, url_prefix='/roadmap')
    app.register_blueprint(progress_bp, url_prefix='/progress')
    app.register_blueprint(interview_bp, url_prefix='/interview')
