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

    def test_mock_ai_evaluates_different_quality_answers(self):
        """Test that MockAIService genuinely analyzes answers with dynamic scoring and feedback."""
        from app.services.mock_ai_service import MockAIService
        service = MockAIService()

        questions = [
            {"id": 1, "question": "Can you describe a challenging technical problem you solved?"},
            {"id": 2, "question": "What are your career goals?"}
        ]

        strong_ans = (
            "In my semester project, I built a high-throughput REST API using FastAPI and PostgreSQL. "
            "Latency was spiking to 450ms during load testing due to unindexed database queries. "
            "I analyzed query execution plans, added composite B-Tree indexes, and introduced a Redis "
            "caching layer. This dropped P99 latency to 35ms and allowed the service to handle 5x more requests."
        )
        weak_ans = "i will study hard and work at google."

        evaluations = service.evaluate_interview_answers(
            questions,
            {"1": strong_ans, "2": weak_ans},
            target_role="Backend Developer"
        )

        self.assertEqual(len(evaluations), 2)
        q1_eval = evaluations[0]
        q2_eval = evaluations[1]

        # Strong answer should score significantly higher than weak answer
        self.assertGreater(q1_eval['score'], q2_eval['score'])
        self.assertGreaterEqual(q1_eval['score'], 8)
        self.assertLessEqual(q2_eval['score'], 5)

        # Technical concepts should be identified in strengths
        self.assertTrue(any("Fastapi" in s or "Postgresql" in s or "Redis" in s or "Api" in s for s in q1_eval['strengths']))

        # Feedback should be dynamic and role-aware
        self.assertIn("Backend Developer", q1_eval['feedback'])
        self.assertIn("Backend Developer", q2_eval['feedback'])

    def test_gemini_extract_json_resilient_parsing(self):
        """Test that GeminiService._extract_json handles lists, objects, and markdown fences."""
        from app.services.gemini_service import GeminiService
        service = GeminiService(api_key="test-key")

        # 1. Markdown code fenced array
        fenced_arr = "```json\n[{\"id\": 1, \"score\": 8}]\n```"
        parsed = service._extract_json(fenced_arr)
        self.assertIsInstance(parsed, list)
        self.assertEqual(parsed[0]['score'], 8)

        # 2. Raw array with surrounding text
        prose_arr = "Here is your evaluation:\n[{\"id\": 1, \"score\": 9}, {\"id\": 2, \"score\": 7}]\nHope this helps!"
        parsed2 = service._extract_json(prose_arr)
        self.assertIsInstance(parsed2, list)
        self.assertEqual(len(parsed2), 2)

        # 3. Standard JSON object
        obj_text = '{"title": "SE Track", "overall_readiness": 85}'
        parsed3 = service._extract_json(obj_text)
        self.assertIsInstance(parsed3, dict)
        self.assertEqual(parsed3['overall_readiness'], 85)

if __name__ == '__main__':
    unittest.main()
