"""
Shared extensions for the Flask application.
Using the factory pattern, these extensions are initialized here
without being bound to the Flask application yet. This prevents
circular dependencies and allows the same extension instance
to be used across multiple apps if needed.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Initialize SQLAlchemy for database interactions
db = SQLAlchemy()

# Initialize Flask-Login for user session management
login_manager = LoginManager()

# Initialize CSRF Protection for non-WTForm POST requests
csrf = CSRFProtect()

# Define the view to redirect unauthorized users to
login_manager.login_view = 'auth.login'

# Set the category for login flash messages
login_manager.login_message_category = 'info'
