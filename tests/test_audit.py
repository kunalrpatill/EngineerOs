"""
Audit Fixes Test Suite.
Tests the Critical and High priority fixes identified during the Final Production-Readiness Audit.
"""
import os
import unittest
from flask import render_template_string
from app import create_app
from app.extensions import db
from app.models.user import User

class AuditFixesTestCase(unittest.TestCase):
    """Test case covering CSRF protection and Custom Error pages."""

    def setUp(self):
        """Set up test application."""
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['SECRET_KEY'] = 'test-secret-key'

        self.app = create_app()
        self.app.config['TESTING'] = True
        
        # Explicitly ENABLE CSRF to test that global protection is active
        self.app.config['WTF_CSRF_ENABLED'] = True
        
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up database after each test."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_user(self):
        """Helper to create a user."""
        with self.app.app_context():
            user = User(name='Audit User', email='audit@example.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()

    def test_global_csrf_rejects_missing_token(self):
        """Test that a POST request to a raw HTML route without a CSRF token is rejected."""
        self._create_user()
        
        # We need a CSRF token to login since WTF_CSRF_ENABLED is True for this test case.
        # But wait, to login programmatically with CSRF enabled, we must fetch the token first.
        # Instead of testing a protected route, let's test a public WTForm route (like /auth/login)
        # and a protected non-WTForm route (we'll just send a POST and expect 400 Bad Request due to CSRF).
        
        # Test 1: POST /auth/login without token should fail with 400
        resp = self.client.post('/auth/login', data={'email': 'audit@example.com', 'password': 'pass123'})
        # WTForms usually handles this by just failing validation, but if CSRFProtect is active, 
        # missing token triggers a 400 Bad Request via Werkzeug HTTP exception.
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b'The CSRF token is missing.', resp.data)

    def test_custom_404_page(self):
        """Test 404 requests return the custom 404 page."""
        resp = self.client.get('/this-route-does-not-exist')
        self.assertEqual(resp.status_code, 404)
        self.assertIn(b'Looks like you\'re off the map!', resp.data)
        self.assertIn(b'Return to Dashboard', resp.data)

    def test_custom_500_page(self):
        """Test 500 errors return the custom 500 page."""
        # To trigger a 500, we can temporarily register a crashing route
        @self.app.route('/crash')
        def crash():
            raise Exception("Simulated Server Error")
            
        # Temporarily disable PROPAGATE_EXCEPTIONS which is sometimes True in testing
        self.app.config['PROPAGATE_EXCEPTIONS'] = False
            
        resp = self.client.get('/crash')
        self.assertEqual(resp.status_code, 500)
        self.assertIn(b'Internal Server Error (500)', resp.data)
        self.assertIn(b'Something went wrong.', resp.data)

if __name__ == '__main__':
    unittest.main()
