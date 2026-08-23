"""
Phase 3 Test Suite for EngineerOS.
Tests AI Skill-Gap Analysis, Mock AI Service, Gemini Service configurations,
Personalized Career Roadmap Generation, DB persistence, and Roadmap Views.
"""
import json
import os
import unittest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill
from app.models.interest import Interest
from app.models.roadmap import Roadmap, RoadmapPhase, Milestone
from app.services.mock_ai_service import MockAIService
from app.services.gemini_service import GeminiService
from app.services.ai_service import get_ai_service


class Phase3TestCase(unittest.TestCase):
    """Test case covering Phase 3 AI Analysis & Career Roadmap Generation."""

    def setUp(self):
        """Set up test application with in-memory SQLite database."""
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['SECRET_KEY'] = 'test-secret-key'
        # Ensure testing uses mock AI by default unless explicitly tested
        os.environ['GEMINI_API_KEY'] = ''
        os.environ['GEMINI_MODEL'] = 'gemini-2.0-flash'

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

    def _create_and_login_user(self, name='Rohan Verma', email='rohan@college.edu', role='Full Stack Developer', skills=None):
        """Helper method to create a student user with a populated profile and log in."""
        with self.app.app_context():
            user = User(name=name, email=email)
            user.set_password('password123')
            db.session.add(user)
            db.session.flush()

            profile = Profile(
                user_id=user.id,
                college='National Institute of Technology',
                branch='Computer Science',
                year=3,
                semester=5,
                cgpa=8.75,
                target_role=role,
                preferred_domain='Web Development',
                career_timeline='6 months'
            )
            db.session.add(profile)

            if skills is None:
                skills = [('Python', 'advanced'), ('HTML/CSS', 'intermediate'), ('JavaScript', 'intermediate')]

            for skill_name, skill_lvl in skills:
                db.session.add(Skill(user_id=user.id, name=skill_name, level=skill_lvl))

            db.session.add(Interest(user_id=user.id, name='Web Development'))
            db.session.commit()
            user_id = user.id

        self.client.post('/auth/login', data={'email': email, 'password': 'password123'}, follow_redirects=True)
        return user_id

    def test_mock_ai_service_analysis_and_roadmap(self):
        """Test MockAIService generates structured analysis and phased roadmap."""
        mock_ai = MockAIService()
        profile_data = {
            'name': 'Rohan Verma',
            'target_role': 'Full Stack Developer',
            'career_timeline': '6 months',
            'skills': ['Python', 'HTML/CSS', 'JavaScript'],
            'interests': ['Web Development']
        }

        # 1. Test skill analysis
        analysis = mock_ai.analyze_skills(profile_data)
        self.assertIn('strong_areas', analysis)
        self.assertIn('gaps_identified', analysis)
        self.assertIn('overall_readiness', analysis)
        self.assertIn('recommendations', analysis)
        self.assertIsInstance(analysis['strong_areas'], list)
        self.assertIsInstance(analysis['gaps_identified'], list)
        self.assertGreater(analysis['overall_readiness'], 0)
        self.assertIn('HTML/CSS', analysis['strong_areas'])

        # 2. Test roadmap generation
        roadmap = mock_ai.generate_roadmap(profile_data)
        self.assertIn('title', roadmap)
        self.assertEqual(roadmap['target_role'], 'Full Stack Developer')
        self.assertIn('phases', roadmap)
        self.assertGreater(len(roadmap['phases']), 0)

        # Check phase & milestone structure
        first_phase = roadmap['phases'][0]
        self.assertIn('phase_number', first_phase)
        self.assertIn('title', first_phase)
        self.assertIn('milestones', first_phase)
        self.assertGreater(len(first_phase['milestones']), 0)

        first_milestone = first_phase['milestones'][0]
        self.assertIn('title', first_milestone)
        self.assertIn('type', first_milestone)
        self.assertIn(first_milestone['type'], ['learning', 'project', 'practice', 'assessment'])

    def test_gemini_service_helper_methods(self):
        """Test GeminiService helper methods and prompt preparation."""
        gemini = GeminiService(api_key='fake-key-for-test', model_name='gemini-2.0-flash')
        self.assertEqual(gemini.model_name, 'gemini-2.0-flash')

        # Test JSON extraction from markdown code block
        sample_json_markdown = '```json\n{"strong_areas": ["Python"], "gaps_identified": ["Docker"], "overall_readiness": 50}\n```'
        extracted = gemini._extract_json(sample_json_markdown)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted['strong_areas'], ['Python'])
        self.assertEqual(extracted['overall_readiness'], 50)

        # Test summary builder
        profile_data = {'name': 'Test', 'target_role': 'AI/ML Engineer', 'skills': ['Python']}
        summary = gemini._build_profile_summary(profile_data)
        self.assertIn('AI/ML Engineer', summary)
        self.assertIn('Python', summary)

    def test_ai_service_factory(self):
        """Test get_ai_service returns MockAIService when no key, and passes model."""
        service = get_ai_service()
        self.assertIsInstance(service, MockAIService)

    def test_roadmap_index_unauthenticated(self):
        """Test that unauthenticated access to /roadmap/ redirects to login."""
        response = self.client.get('/roadmap/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)

    def test_roadmap_generate_requires_target_role_and_skills(self):
        """Test roadmap generation redirects with warning if target role or skills are missing."""
        # 1. Create student with NO target role and NO skills
        with self.app.app_context():
            user = User(name='Incomplete Student', email='incomplete@college.edu')
            user.set_password('pass123')
            db.session.add(user)
            db.session.flush()
            db.session.add(Profile(user_id=user.id, target_role=''))
            db.session.commit()

        self.client.post('/auth/login', data={'email': 'incomplete@college.edu', 'password': 'pass123'}, follow_redirects=True)

        # Try to generate roadmap
        resp = self.client.post('/roadmap/generate', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'target career role', resp.data)

    def test_roadmap_generate_and_store_in_database(self):
        """Test complete roadmap generation, database storage, and view rendering."""
        user_id = self._create_and_login_user()

        # 1. Generate roadmap via POST
        response = self.client.post('/roadmap/generate', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'personalized career roadmap has been generated', response.data)
        self.assertIn(b'Full Stack Developer', response.data)
        self.assertIn(b'Phased Learning Path', response.data)

        # 2. Verify in database
        with self.app.app_context():
            roadmap = Roadmap.query.filter_by(user_id=user_id, is_active=True).first()
            self.assertIsNotNone(roadmap)
            self.assertEqual(roadmap.target_role, 'Full Stack Developer')
            self.assertTrue(roadmap.is_active)
            self.assertGreater(roadmap.overall_readiness, 0)

            # Verify stored JSON
            strong_areas = json.loads(roadmap.strong_areas)
            self.assertIsInstance(strong_areas, list)
            self.assertIn('Python', strong_areas)

            # Verify phases & milestones in DB
            phases = RoadmapPhase.query.filter_by(roadmap_id=roadmap.id).all()
            self.assertGreater(len(phases), 0)

            first_phase = phases[0]
            milestones = Milestone.query.filter_by(phase_id=first_phase.id).all()
            self.assertGreater(len(milestones), 0)

    def test_roadmap_regeneration_deactivates_previous(self):
        """Test generating a new roadmap deactivates the previous one."""
        user_id = self._create_and_login_user()

        # Generate first roadmap
        self.client.post('/roadmap/generate', follow_redirects=True)

        # Generate second roadmap
        self.client.post('/roadmap/generate', follow_redirects=True)

        with self.app.app_context():
            roadmaps = Roadmap.query.filter_by(user_id=user_id).order_by(Roadmap.id.asc()).all()
            self.assertEqual(len(roadmaps), 2)
            self.assertFalse(roadmaps[0].is_active)  # First is now inactive
            self.assertTrue(roadmaps[1].is_active)   # Second is active

    def test_roadmap_view_authorization(self):
        """Test a student cannot view another student's roadmap."""
        user1_id = self._create_and_login_user(name='Student One', email='s1@eng.edu')
        self.client.post('/roadmap/generate', follow_redirects=True)

        with self.app.app_context():
            s1_roadmap = Roadmap.query.filter_by(user_id=user1_id).first()
            s1_roadmap_id = s1_roadmap.id

        # Log out student 1, log in student 2
        self.client.get('/auth/logout', follow_redirects=True)
        self._create_and_login_user(name='Student Two', email='s2@eng.edu')

        # Student 2 tries to access Student 1's roadmap
        resp = self.client.get(f'/roadmap/{s1_roadmap_id}', follow_redirects=True)
        self.assertIn(b'Roadmap not found', resp.data)


if __name__ == '__main__':
    unittest.main()
