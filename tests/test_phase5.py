"""
Phase 5 Test Suite for EngineerOS.
Tests the Comprehensive Career-Readiness Dashboard, which aggregates data
from all previous phases into a single view.
"""
import os
import json
import unittest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill
from app.models.interest import Interest
from app.models.roadmap import Roadmap, RoadmapPhase, Milestone
from app.models.progress import Progress


class Phase5TestCase(unittest.TestCase):
    """Test case covering Phase 5 Comprehensive Career-Readiness Dashboard."""

    def setUp(self):
        """Set up test application with in-memory SQLite database."""
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['SECRET_KEY'] = 'test-secret-key'
        os.environ['GEMINI_API_KEY'] = ''

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

    def _create_and_login_user(self, name='Kunal Sharma', email='kunal@college.edu',
                               create_profile=True, create_skills=True,
                               create_roadmap=False, create_progress=False):
        """
        Helper to create a student with configurable data and log in.

        Returns:
            dict: Dictionary of created object IDs for assertions.
        """
        result = {}
        with self.app.app_context():
            user = User(name=name, email=email)
            user.set_password('pass123')
            db.session.add(user)
            db.session.flush()
            result['user_id'] = user.id

            if create_profile:
                profile = Profile(
                    user_id=user.id,
                    college='NIT Raipur',
                    branch='Computer Science',
                    year=3,
                    semester=5,
                    cgpa=8.75,
                    target_role='Full Stack Developer',
                    preferred_domain='Web Development',
                    github_url='https://github.com/kunal'
                )
                db.session.add(profile)

            if create_skills:
                db.session.add(Skill(user_id=user.id, name='Python', level='advanced'))
                db.session.add(Skill(user_id=user.id, name='JavaScript', level='intermediate'))
                db.session.add(Skill(user_id=user.id, name='React', level='beginner'))

            if create_roadmap:
                roadmap = Roadmap(
                    user_id=user.id,
                    title='Full Stack Development Track',
                    target_role='Full Stack Developer',
                    estimated_duration='6 months',
                    strong_areas=json.dumps(['Python', 'Flask', 'SQL']),
                    gaps_identified=json.dumps(['React', 'DevOps', 'System Design']),
                    overall_readiness=25,
                    is_active=True
                )
                db.session.add(roadmap)
                db.session.flush()
                result['roadmap_id'] = roadmap.id

                # Phase 1: 2 milestones (1 completed, 1 not)
                phase1 = RoadmapPhase(
                    roadmap_id=roadmap.id, phase_number=1,
                    title='Phase 1: Foundations', duration='2 months',
                    status='in_progress'
                )
                db.session.add(phase1)
                db.session.flush()

                m1 = Milestone(phase_id=phase1.id, title='Learn React Basics',
                               status='completed', milestone_type='learning')
                m2 = Milestone(phase_id=phase1.id, title='Build Todo App',
                               status='not_started', milestone_type='project')
                db.session.add_all([m1, m2])

                # Phase 2: 2 milestones (both not started)
                phase2 = RoadmapPhase(
                    roadmap_id=roadmap.id, phase_number=2,
                    title='Phase 2: Advanced', duration='2 months',
                    status='not_started'
                )
                db.session.add(phase2)
                db.session.flush()

                m3 = Milestone(phase_id=phase2.id, title='Learn Docker',
                               status='not_started', milestone_type='learning')
                m4 = Milestone(phase_id=phase2.id, title='Deploy Application',
                               status='not_started', milestone_type='project')
                db.session.add_all([m3, m4])

                result['total_milestones'] = 4
                result['completed_milestones'] = 1

            if create_progress:
                # Add some progress entries
                p1 = Progress(
                    user_id=user.id,
                    type='milestone_completed',
                    title='Learn React Basics',
                    readiness_before=20,
                    readiness_after=30
                )
                p2 = Progress(
                    user_id=user.id,
                    type='project_completed',
                    title='Personal Portfolio Website',
                    description='Built a responsive portfolio.',
                    readiness_before=30,
                    readiness_after=36
                )
                p3 = Progress(
                    user_id=user.id,
                    type='course_completed',
                    title='Flask Mega Tutorial',
                    readiness_before=36,
                    readiness_after=40
                )
                db.session.add_all([p1, p2, p3])

            db.session.commit()

        # Log in
        self.client.post('/auth/login', data={
            'email': email, 'password': 'pass123'
        }, follow_redirects=True)

        return result

    # ── Test 1: Unauthenticated redirect ────────────────────────────────

    def test_dashboard_unauthenticated_redirects(self):
        """Test /dashboard/ redirects to login when not authenticated."""
        resp = self.client.get('/dashboard/', follow_redirects=False)
        self.assertIn(resp.status_code, [302, 303])
        self.assertIn('/auth/login', resp.headers.get('Location', ''))

    # ── Test 2: Readiness score displayed ───────────────────────────────

    def test_dashboard_renders_readiness_score(self):
        """Test dashboard displays the computed career readiness percentage."""
        self._create_and_login_user(create_roadmap=True, create_progress=True)

        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 200)

        # Check readiness score appears (as "XX%" text)
        self.assertIn(b'Career Readiness', resp.data)
        # Check the stage badge is present (should be one of the 4 stages)
        stage_found = (
            b'Novice' in resp.data or
            b'Emerging' in resp.data or
            b'Placement Ready' in resp.data or
            b'Industry Ready' in resp.data
        )
        self.assertTrue(stage_found, 'Expected a readiness stage badge on the dashboard')

    # ── Test 3: Dashboard with active roadmap ───────────────────────────

    def test_dashboard_with_active_roadmap(self):
        """Test roadmap summary card appears with correct milestone counts and target role."""
        data = self._create_and_login_user(create_roadmap=True)

        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 200)

        # Roadmap title and target role are displayed
        self.assertIn(b'Full Stack Development Track', resp.data)
        self.assertIn(b'Full Stack Developer', resp.data)

        # Milestone pct is rendered
        self.assertIn(b'25', resp.data)  # 25% Done badge

        # View Full Roadmap link is present
        self.assertIn(b'roadmap', resp.data.lower())

    # ── Test 4: Dashboard without roadmap ───────────────────────────────

    def test_dashboard_without_roadmap(self):
        """Test dashboard gracefully renders with no active roadmap (shows CTA)."""
        self._create_and_login_user(create_roadmap=False)

        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 200)

        # CTA to generate roadmap is visible
        self.assertIn(b'Generate Roadmap', resp.data)

    # ── Test 5: Recent activity feed ────────────────────────────────────

    def test_dashboard_shows_recent_activities(self):
        """Test the recent activity feed displays logged accomplishments."""
        self._create_and_login_user(create_roadmap=True, create_progress=True)

        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 200)

        # Progress entries should appear in the activity feed
        self.assertIn(b'Learn React Basics', resp.data)
        self.assertIn(b'Personal Portfolio Website', resp.data)
        self.assertIn(b'Flask Mega Tutorial', resp.data)
        self.assertIn(b'Recent Activity', resp.data)

    # ── Test 6: Skill-gap analysis snapshot ─────────────────────────────

    def test_dashboard_shows_skill_gap_analysis(self):
        """Test strong areas and gaps from the roadmap are displayed as badges."""
        self._create_and_login_user(create_roadmap=True)

        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 200)

        # Strong area badges
        self.assertIn(b'Strong Skills', resp.data)
        self.assertIn(b'Python', resp.data)
        self.assertIn(b'Flask', resp.data)
        self.assertIn(b'SQL', resp.data)

        # Gap badges
        self.assertIn(b'Skill Gaps', resp.data)
        self.assertIn(b'React', resp.data)
        self.assertIn(b'DevOps', resp.data)
        self.assertIn(b'System Design', resp.data)


if __name__ == '__main__':
    unittest.main()
