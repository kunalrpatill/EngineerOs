"""
Application Factory module.
This module contains the create_app function which sets up the Flask application.
"""
import os
import sys
from flask import Flask
from dotenv import load_dotenv

def create_app():
    """
    App factory function.
    Creates and configures the Flask application.
    
    This pattern lets us create multiple app instances (useful for testing)
    and keeps setup logic organized in one place.
    """
    # 1. Load .env file FIRST so environment variables are available for Config
    load_dotenv()
    
    # 2. Create Flask app
    app = Flask(__name__)
    
    # 3. Load config from app.config.Config (reads env vars set by load_dotenv)
    from app.config import Config
    app.config.from_object(Config)
    
    # 4. Initialize extensions with the app
    from app.extensions import db, login_manager, csrf
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # 5. Register blueprints
    from app.routes import register_blueprints
    register_blueprints(app)
    
    # 6. Import all models and create database tables
    with app.app_context():
        from app import models  # noqa: F401
        
        # 7. Try to create tables — if MySQL isn't running, warn but don't crash
        try:
            db.create_all()
            print(" * Database tables created/verified successfully.")
        except Exception as e:
            print("\n" + "=" * 60)
            print(" WARNING: Could not connect to MySQL database!")
            print("=" * 60)
            print(f" Error: {e}")
            print("\n Make sure:")
            print("   1. XAMPP is running and MySQL is started")
            print("   2. The database 'engineeros_db' exists in phpMyAdmin")
            print("   3. Your .env file has the correct DB credentials")
            print("\n The app will start, but database features won't work")
            print("  until MySQL is available.")
            print("=" * 60 + "\n")
        
    return app


