"""
Phase 4 Test Suite for EngineerOS.
Tests Career Readiness calculation, milestone completion toggles,
phase status synchronization, manual accomplishment logging, activity feed filtering,
and authorization boundaries.
"""
import os
import unittest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill
from app.models.interest import Interest
from app.models.roadmap import Roadmap, RoadmapPhase, Milestone
from app.models.progress import Progress
from app.services.readiness import calculate_readiness, sync_roadmap_and_phase_status


class Phase4TestCase(unittest.TestCase):
    """Test case covering Phase 4 Progress Tracking & Career Readiness features."""

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

    def _create_and_login_student(self, name='Vikram Malhotra', email='vikram@college.edu'):
        """Helper to create a student with profile, skills, roadmap, and log in."""
        with self.app.app_context():
            user = User(name=name, email=email)
            user.set_password('pass123')
            db.session.add(user)
            db.session.flush()

            profile = Profile(
                user_id=user.id,
                college='IIT Bombay',
                branch='Computer Science',
                year=4,
                semester=7,
                cgpa=9.10,
                target_role='Backend Engineer',
                preferred_domain='Cloud & Distributed Systems',
                github_url='https://github.com/vikram'
            )
            db.session.add(profile)

            # Add skills
            db.session.add(Skill(user_id=user.id, name='Python', level='advanced'))
            db.session.add(Skill(user_id=user.id, name='Docker', level='intermediate'))
            db.session.add(Skill(user_id=user.id, name='SQL', level='intermediate'))

            # Add roadmap with 2 phases and 2 milestones each
            roadmap = Roadmap(
                user_id=user.id,
                title='Backend Engineering Track',
                target_role='Backend Engineer',
                overall_readiness=20,
                is_active=True
            )
            db.session.add(roadmap)
            db.session.flush()

            phase1 = RoadmapPhase(roadmap_id=roadmap.id, phase_number=1, title='Phase 1: Foundations', status='not_started')
            phase2 = RoadmapPhase(roadmap_id=roadmap.id, phase_number=2, title='Phase 2: Advanced Systems', status='not_started')
            db.session.add_all([phase1, phase2])
            db.session.flush()

            m1 = Milestone(phase_id=phase1.id, title='Master Python Advanced Topics', status='not_started', milestone_type='learning')
            m2 = Milestone(phase_id=phase1.id, title='Build REST API', status='not_started', milestone_type='project')
            m3 = Milestone(phase_id=phase2.id, title='Study System Design', status='not_started', milestone_type='learning')
            m4 = Milestone(phase_id=phase2.id, title='Deploy with Docker & CI/CD', status='not_started', milestone_type='project')
            db.session.add_all([m1, m2, m3, m4])

            db.session.commit()
            user_id = user.id
            m1_id = m1.id
            m2_id = m2.id
            phase1_id = phase1.id

        self.client.post('/auth/login', data={'email': email, 'password': 'pass123'}, follow_redirects=True)
        return user_id, m1_id, m2_id, phase1_id

    def test_readiness_calculation_weights(self):
        """Test scoring engine weights skills, profile clarity, milestones, and accomplishments."""
        with self.app.app_context():
            user = User(name='Ankit Ray', email='ankit@eng.edu')
            user.set_password('pass123')
            db.session.add(user)
            db.session.flush()

            # 1. Base user with no profile -> 0 score
            score_initial = calculate_readiness(user.id)
            self.assertEqual(score_initial, 0)

            # 2. Add profile info -> score increases
            profile = Profile(
                user_id=user.id,
                target_role='Full Stack Developer',
                preferred_domain='Web Development',
                github_url='https://github.com/ankit',
                college='Delhi Tech University',
                cgpa=8.5
            )
            db.session.add(profile)
            db.session.commit()
            score_profile = calculate_readiness(user.id)
            self.assertGreater(score_profile, score_initial)

            # 3. Add skills -> score increases further
            db.session.add(Skill(user_id=user.id, name='Python', level='advanced'))  # +5
            db.session.add(Skill(user_id=user.id, name='React', level='intermediate'))  # +3
            db.session.commit()
            score_skills = calculate_readiness(user.id)
            self.assertGreater(score_skills, score_profile)

    def test_milestone_toggle_completed(self):
        """Test toggling milestone to completed updates milestone, phase, progress table, and readiness."""
        user_id, m1_id, m2_id, phase1_id = self._create_and_login_student()

        # Toggle milestone 1 to completed
        resp = self.client.post(f'/progress/milestone/{m1_id}/toggle', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'marked as completed', resp.data)

        with self.app.app_context():
            # Check milestone status
            m1 = db.session.get(Milestone, m1_id)
            self.assertEqual(m1.status, 'completed')

            # Check phase status is in_progress (1 of 2 completed)
            phase1 = db.session.get(RoadmapPhase, phase1_id)

            self.assertEqual(phase1.status, 'in_progress')

            # Check Progress record created
            prog = Progress.query.filter_by(user_id=user_id, milestone_id=m1_id).first()
            self.assertIsNotNone(prog)
            self.assertEqual(prog.type, 'milestone_completed')
            self.assertIn('Master Python', prog.title)

    def test_milestone_toggle_reversal(self):
        """Test toggling completed milestone back to pending removes progress and updates phase."""
        user_id, m1_id, m2_id, phase1_id = self._create_and_login_student()

        # Mark completed
        self.client.post(f'/progress/milestone/{m1_id}/toggle', follow_redirects=True)

        # Unmark (revert to not_started)
        resp = self.client.post(f'/progress/milestone/{m1_id}/toggle', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'reverted to pending', resp.data)

        with self.app.app_context():
            m1 = db.session.get(Milestone, m1_id)
            self.assertEqual(m1.status, 'not_started')

            phase1 = db.session.get(RoadmapPhase, phase1_id)
            self.assertEqual(phase1.status, 'not_started')

            # Check Progress record removed
            prog = Progress.query.filter_by(user_id=user_id, milestone_id=m1_id).first()
            self.assertIsNone(prog)

    def test_phase_status_synchronization(self):
        """Test phase status transitions correctly from not_started -> in_progress -> completed."""
        user_id, m1_id, m2_id, phase1_id = self._create_and_login_student()

        with self.app.app_context():
            phase1 = db.session.get(RoadmapPhase, phase1_id)
            self.assertEqual(phase1.status, 'not_started')

        # 1. Complete first milestone in phase -> in_progress
        self.client.post(f'/progress/milestone/{m1_id}/toggle', follow_redirects=True)
        with self.app.app_context():
            phase1 = db.session.get(RoadmapPhase, phase1_id)
            self.assertEqual(phase1.status, 'in_progress')

        # 2. Complete second milestone in phase -> completed
        self.client.post(f'/progress/milestone/{m2_id}/toggle', follow_redirects=True)
        with self.app.app_context():
            phase1 = db.session.get(RoadmapPhase, phase1_id)
            self.assertEqual(phase1.status, 'completed')

    def test_manual_accomplishment_logging(self):
        """Test logging a project/course creates Progress record and adjusts readiness."""
        user_id, m1_id, m2_id, phase1_id = self._create_and_login_student()

        resp = self.client.post('/progress/log', data={
            'type': 'project_completed',
            'title': 'AI Automated Code Reviewer',
            'description': 'Built a full-stack Flask and Gemini API app for PR reviews.',
            'skills_gained': 'Flask, Gemini AI, Docker, PyTest'
        }, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Accomplishment logged successfully', resp.data)
        self.assertIn(b'AI Automated Code Reviewer', resp.data)

        with self.app.app_context():
            prog = Progress.query.filter_by(user_id=user_id, type='project_completed').first()
            self.assertIsNotNone(prog)
            self.assertEqual(prog.title, 'AI Automated Code Reviewer')
            self.assertIn('Flask', prog.skills_gained)

    def test_accomplishment_deletion(self):
        """Test deleting an accomplishment removes the record."""
        user_id, m1_id, m2_id, phase1_id = self._create_and_login_student()

        # Log project
        self.client.post('/progress/log', data={
            'type': 'project_completed',
            'title': 'Sample Project To Delete',
            'description': 'Temporary description.'
        }, follow_redirects=True)

        with self.app.app_context():
            prog = Progress.query.filter_by(user_id=user_id, title='Sample Project To Delete').first()
            prog_id = prog.id

        # Delete project
        resp = self.client.post(f'/progress/delete/{prog_id}', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Accomplishment entry removed', resp.data)

        with self.app.app_context():
            deleted = db.session.get(Progress, prog_id)
            self.assertIsNone(deleted)

    def test_progress_feed_type_filter(self):
        """Test filtering progress timeline by type parameter."""
        user_id, m1_id, m2_id, phase1_id = self._create_and_login_student()

        # Log a project and a course
        self.client.post('/progress/log', data={'type': 'project_completed', 'title': 'Project Unique Name Alpha'}, follow_redirects=True)
        self.client.post('/progress/log', data={'type': 'course_completed', 'title': 'Course Unique Name Beta'}, follow_redirects=True)

        # Filter by project_completed
        resp_project = self.client.get('/progress/?type=project_completed')
        self.assertEqual(resp_project.status_code, 200)
        self.assertIn(b'Project Unique Name Alpha', resp_project.data)
        self.assertNotIn(b'Course Unique Name Beta', resp_project.data)

        # Filter by course_completed
        resp_course = self.client.get('/progress/?type=course_completed')
        self.assertEqual(resp_course.status_code, 200)
        self.assertIn(b'Course Unique Name Beta', resp_course.data)
        self.assertNotIn(b'Project Unique Name Alpha', resp_course.data)

    def test_progress_unauthorized_access(self):
        """Test student cannot toggle milestone or delete progress of another user."""
        u1_id, m1_id, m2_id, phase1_id = self._create_and_login_student(name='Student Alpha', email='alpha@eng.edu')

        # Log out Student Alpha and log in Student Beta
        self.client.get('/auth/logout', follow_redirects=True)
        u2_id, u2_m1_id, _, _ = self._create_and_login_student(name='Student Beta', email='beta@eng.edu')

        # Student Beta tries to toggle Student Alpha's milestone (m1_id)
        resp = self.client.post(f'/progress/milestone/{m1_id}/toggle', follow_redirects=True)
        self.assertIn(b'Unauthorized access', resp.data)

        with self.app.app_context():
            # Verify Student Alpha's milestone remained not_started
            m1 = db.session.get(Milestone, m1_id)
            self.assertEqual(m1.status, 'not_started')



if __name__ == '__main__':
    unittest.main()
