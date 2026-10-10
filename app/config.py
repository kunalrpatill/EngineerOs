import os

class Config:
    """
    Configuration class for the Flask application.
    Loads settings from environment variables with sensible defaults.
    """
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-fallback')
    
    # Database connection settings from environment variables
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'engineeros_db')
    
    # Construct the SQLAlchemy database URI for MySQL using PyMySQL
    # Can also be overridden directly via DATABASE_URL if set
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    # Disable tracking modifications to save memory and improve performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
    "connect_args": {
        "ssl": {"check_hostname": True}
    }
}
    
    # Optional Gemini AI API Key, empty string by default
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    
    # Gemini model name — configurable via .env (default: gemini-2.0-flash)
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
