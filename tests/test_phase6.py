"""
Phase 6 Test Suite for EngineerOS.
Tests the AI Interview Prep engine, including generation, validation, and evaluation.
"""
import os
import unittest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.profile import Profile
from app.models.roadmap import Roadmap

class Phase6TestCase(unittest.TestCase):
    """Test case covering Phase 6 AI Mock Interview Engine."""

    def setUp(self):
        """Set up test application with in-memory SQLite database."""
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['SECRET_KEY'] = 'test-secret-key'
        os.environ['GEMINI_API_KEY'] = '' # Force Mock AI for predictable tests

        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up database after each test."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_and_login_user(self, has_profile=True, has_target_role=True, email='test@example.com'):
        """Helper to create a user and log in."""
        with self.app.app_context():
            user = User(name='Test User', email=email)
            user.set_password('pass123')
            db.session.add(user)
            db.session.flush()

            if has_profile:
                profile = Profile(
                    user_id=user.id,
                    target_role='Software Engineer' if has_target_role else ''
                )
                db.session.add(profile)
                
                # Create active roadmap
                roadmap = Roadmap(
                    user_id=user.id,
                    title='SE Track',
                    target_role='Software Engineer',
                    gaps_identified='["Docker", "React"]',
                    is_active=True
                )
                db.session.add(roadmap)

            db.session.commit()

        self.client.post('/auth/login', data={'email': email, 'password': 'pass123'}, follow_redirects=True)

    def test_interview_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        resp = self.client.get('/interview/', follow_redirects=False)
        self.assertIn(resp.status_code, [302, 303])
        self.assertIn(b'/auth/login', resp.headers.get('Location', '').encode())

    def test_interview_requires_profile_and_target_role(self):
        """Test index redirects if profile or target_role is missing."""
        self._create_and_login_user(has_profile=True, has_target_role=False, email='test1@example.com')
        resp = self.client.get('/interview/', follow_redirects=False)
        self.assertIn(resp.status_code, [302, 303])
        # Should redirect to dashboard
        self.assertIn(b'/dashboard', resp.headers.get('Location', '').encode())

    def test_interview_loads_with_proper_profile(self):
        """Test index loads successfully with proper profile."""
        self._create_and_login_user(has_profile=True, has_target_role=True, email='test2@example.com')
        resp2 = self.client.get('/interview/')
        self.assertEqual(resp2.status_code, 200)
        self.assertIn(b'AI-Powered', resp2.data)

    def test_mock_ai_generate_questions(self):
        """Test POST /generate uses Mock AI to set session questions."""
        self._create_and_login_user()
        
        with self.client as c:
            resp = c.post('/interview/generate', follow_redirects=False)
            self.assertIn(resp.status_code, [302, 303])
            self.assertIn(b'/interview/session', resp.headers.get('Location', '').encode())
            
            with c.session_transaction() as sess:
                questions = sess.get('interview_questions')
                self.assertIsNotNone(questions)
                self.assertTrue(isinstance(questions, list))
                self.assertGreater(len(questions), 0)
                self.assertIn('id', questions[0])
                self.assertIn('question', questions[0])

    def test_interview_session_view(self):
        """Test GET /session renders generated questions."""
        self._create_and_login_user()
        
        with self.client as c:
            c.post('/interview/generate')
            resp = c.get('/interview/session')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Mock Interview', resp.data)
            self.assertIn(b'<textarea', resp.data)

    def test_interview_session_missing(self):
        """Test GET /session redirects if no questions in session."""
        self._create_and_login_user()
        resp = self.client.get('/interview/session', follow_redirects=True)
        self.assertIn(b'No active interview session found', resp.data)

    def test_submit_empty_or_malformed_answers(self):
        """Test POST /submit handles empty answers appropriately."""
        self._create_and_login_user()
        
        with self.client as c:
            c.post('/interview/generate')
            
            # Submit empty answers
            resp = c.post('/interview/submit', data={
                'answer_1': '   ', # Just spaces
                'answer_2': 'Good answer'
            }, follow_redirects=True)
            
            # Should flash error and stay on session page
            self.assertIn(b'Please provide an answer for all questions', resp.data)
            
            with c.session_transaction() as sess:
                self.assertIsNotNone(sess.get('interview_questions'))

    def test_mock_ai_evaluate_answers_and_clear_session(self):
        """Test valid POST /submit evaluates answers and clears session."""
        self._create_and_login_user()
        
        with self.client as c:
            c.post('/interview/generate')
            
            with c.session_transaction() as sess:
                questions = sess.get('interview_questions')
            
            # Build valid answer form data
            data = {}
            for q in questions:
                data[f"answer_{q['id']}"] = f"This is a solid mock answer for question {q['id']}."
                
            resp = c.post('/interview/submit', data=data, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            
            # Verify feedback rendered
            self.assertIn(b'Interview Evaluation', resp.data)
            self.assertIn(b'AI Evaluation', resp.data)
            self.assertIn(b'Strengths', resp.data)
            
            # Verify session is cleared
            with c.session_transaction() as sess:
                self.assertIsNone(sess.get('interview_questions'))

    def test_gemini_failure_fallback_integration(self):
        """Test the system doesn't crash if Gemini is enabled but fails."""
        # Force a bad API key to trigger fallback
        os.environ['GEMINI_API_KEY'] = 'fake-bad-key'
        self._create_and_login_user()
        
        with self.client as c:
            # Generate should gracefully fall back to mock
            c.post('/interview/generate')
            with c.session_transaction() as sess:
                questions = sess.get('interview_questions')
                self.assertIsNotNone(questions)
                
            # Submit should gracefully fall back to mock
            data = {f"answer_{q['id']}": "Fallback test answer" for q in questions}
            resp = c.post('/interview/submit', data=data, follow_redirects=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'AI Evaluation', resp.data)

if __name__ == '__main__':
    unittest.main()
