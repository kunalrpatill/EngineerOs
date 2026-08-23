from flask import Blueprint, render_template

# Public landing page blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Public landing page"""
    return render_template('home.html')

@main_bp.app_errorhandler(404)
def page_not_found(e):
    """Handle 404 errors globally"""
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors globally"""
    return render_template('errors/500.html'), 500
