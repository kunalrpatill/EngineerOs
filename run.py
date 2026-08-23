"""
Main entry point for the EngineerOS application.
This file imports the app factory, creates the Flask application,
and runs the development server.
"""
from app import create_app
import os

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    # Run the application on port 5000
    # Debug mode is controlled by the FLASK_DEBUG environment variable
    app.run(port=5000, debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')
