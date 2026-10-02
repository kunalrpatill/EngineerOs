import os
import unittest
import json
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.practice import PracticeQuestion, PracticeAttempt
from app.models.roadmap import Roadmap, RoadmapPhase, Milestone

class PracticeArenaTestCase(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['SECRET_KEY'] = 'test-secret-key'

        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self._create_user()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_user(self):
        user = User(name='Test Student', email='teststudent@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        self.user_id = user.id

    def login(self):
        return self.client.post('/auth/login', data=dict(
            email='teststudent@example.com',
            password='password123'
        ), follow_redirects=True)

    def test_practice_arena_unauthenticated(self):
        response = self.client.get('/practice/')
        self.assertEqual(response.status_code, 302)
        location = response.headers.get('Location', '').lower()
        self.assertTrue('/auth/login' in location)

    def test_practice_arena_authenticated(self):
        self.login()
        response = self.client.get('/practice/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Practice Arena', response.data)

    def test_roadmap_matching_and_verified(self):
        with self.app.app_context():
            roadmap = Roadmap(user_id=self.user_id, title="Java Developer", target_role="Backend Developer")
            db.session.add(roadmap)
            db.session.commit()

            phase = RoadmapPhase(roadmap_id=roadmap.id, title="Basics", phase_number=1)
            db.session.add(phase)
            db.session.commit()

            milestone = Milestone(phase_id=phase.id, title="OOP", status="in_progress")
            db.session.add(milestone)
            db.session.commit()

            q1 = PracticeQuestion(
                title="What is inheritance?", description="desc", language="Java",
                topic="OOP", difficulty="Easy", question_type="MCQ",
                correct_answer="Mechanism", verified=True
            )
            q2 = PracticeQuestion(
                title="What is polymorhpism?", description="desc", language="Java",
                topic="OOP", difficulty="Easy", question_type="MCQ",
                correct_answer="Many forms", verified=False
            )
            q3 = PracticeQuestion(
                title="What is SQL?", description="desc", language="SQL",
                topic="Databases", difficulty="Easy", question_type="MCQ",
                correct_answer="Language", verified=True
            )
            
            db.session.add_all([q1, q2, q3])
            db.session.commit()

        self.login()
        response = self.client.get('/practice/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Current Roadmap Topic:', response.data)
        self.assertIn(b'OOP', response.data)
        
        self.assertIn(b'What is inheritance?', response.data)
        self.assertNotIn(b'What is polymorhpism?', response.data)
        
    def test_question_submission(self):
        with self.app.app_context():
            q1 = PracticeQuestion(
                title="Q1", description="desc", language="Java",
                topic="OOP", difficulty="Easy", question_type="MCQ",
                correct_answer="CorrectOption", verified=True
            )
            db.session.add(q1)
            db.session.commit()
            q1_id = q1.id

        self.login()
        
        response = self.client.get(f'/practice/question/{q1_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Submit Answer', response.data)

        response = self.client.post(f'/practice/submit/{q1_id}', data={'answer': 'CorrectOption'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Correct Answer', response.data)

        with self.app.app_context():
            attempts = PracticeAttempt.query.filter_by(user_id=self.user_id).all()
            self.assertEqual(len(attempts), 1)
            self.assertTrue(attempts[0].result)
            self.assertTrue(attempts[0].completed_status)
            self.assertEqual(attempts[0].attempt_count, 1)

    def test_repeated_submissions(self):
        with self.app.app_context():
            q1 = PracticeQuestion(
                title="Q1", description="desc", language="Java",
                topic="OOP", difficulty="Easy", question_type="MCQ",
                correct_answer="CorrectOption", verified=True
            )
            db.session.add(q1)
            db.session.commit()
            q1_id = q1.id

        self.login()
        
        self.client.post(f'/practice/submit/{q1_id}', data={'answer': 'Wrong'})
        self.client.post(f'/practice/submit/{q1_id}', data={'answer': 'CorrectOption'})
        self.client.post(f'/practice/submit/{q1_id}', data={'answer': 'CorrectOption'})

        with self.app.app_context():
            attempts = PracticeAttempt.query.filter_by(user_id=self.user_id, question_id=q1_id).all()
            self.assertEqual(len(attempts), 1)
            self.assertEqual(attempts[0].attempt_count, 3)
            self.assertTrue(attempts[0].completed_status)

if __name__ == '__main__':
    unittest.main()
