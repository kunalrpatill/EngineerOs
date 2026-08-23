"""
Phase 2 Test Suite for EngineerOS.
Tests user registration, login, logout, protected routes,
profile viewing, profile editing, dynamic skills, interests, and completion calculation.
"""
import os
import unittest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill
from app.models.interest import Interest
from app.utils.completion import calculate_profile_completion


class Phase2TestCase(unittest.TestCase):
    """Test case covering Phase 2 features."""

    def setUp(self):
        """Set up test application with an in-memory SQLite database."""
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['SECRET_KEY'] = 'test-secret-key'
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for programmatic testing
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up database after each test."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_registration_success(self):
        """Test successful registration creates user and profile."""
        response = self.client.post('/auth/register', data={
            'name': 'Kunal Sharma',
            'email': 'kunal@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)

        with self.app.app_context():
            user = User.query.filter_by(email='kunal@example.com').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.name, 'Kunal Sharma')
            self.assertTrue(user.check_password('password123'))
            self.assertFalse(user.check_password('wrongpass'))

            # Check initial blank profile was created
            self.assertIsNotNone(user.profile)
            self.assertEqual(user.profile.completion_percentage, 0)

    def test_registration_duplicate_email(self):
        """Test registration rejects duplicate email."""
        with self.app.app_context():
            user = User(name='Existing User', email='existing@example.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()

        response = self.client.post('/auth/register', data={
            'name': 'Another User',
            'email': 'existing@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'account with this email address already exists', response.data)

    def test_login_and_logout(self):
        """Test user login and session logout."""
        # 1. Register user
        with self.app.app_context():
            user = User(name='Alex Student', email='alex@college.edu')
            user.set_password('securepass')
            db.session.add(user)
            db.session.commit()

        # 2. Test failed login
        response = self.client.post('/auth/login', data={
            'email': 'alex@college.edu',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', response.data)

        # 3. Test successful login
        response = self.client.post('/auth/login', data={
            'email': 'alex@college.edu',
            'password': 'securepass'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back, Alex Student!', response.data)

        # 4. Access protected dashboard
        dash_response = self.client.get('/dashboard/')
        self.assertEqual(dash_response.status_code, 200)
        self.assertIn(b'Alex Student', dash_response.data)

        # 5. Test logout
        logout_response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(logout_response.status_code, 200)
        self.assertIn(b'signed out successfully', logout_response.data)

        # 6. Dashboard should now redirect to login
        dash_after_logout = self.client.get('/dashboard/')
        self.assertEqual(dash_after_logout.status_code, 302)
        self.assertIn('/auth/login', dash_after_logout.location)

    def test_protected_routes_require_login(self):
        """Test that unauthenticated access to protected routes redirects to login."""
        protected_urls = ['/dashboard/', '/profile/', '/profile/edit', '/roadmap/', '/progress/']
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f"Failed for url: {url}")
            self.assertIn('/auth/login', response.location)

    def test_profile_view_and_edit(self):
        """Test profile viewing and updating with skills and interests."""
        # 1. Create and login user
        with self.app.app_context():
            user = User(name='Priya Patel', email='priya@eng.edu')
            user.set_password('priyapass')
            db.session.add(user)
            db.session.flush()
            profile = Profile(user_id=user.id)
            db.session.add(profile)
            db.session.commit()

        self.client.post('/auth/login', data={
            'email': 'priya@eng.edu',
            'password': 'priyapass'
        }, follow_redirects=True)

        # 2. View empty profile
        view_resp = self.client.get('/profile/')
        self.assertEqual(view_resp.status_code, 200)
        self.assertIn(b'Priya Patel', view_resp.data)

        # 3. Update profile with academic, career, and dynamic skill/interest data
        edit_resp = self.client.post('/profile/edit', data={
            'college': 'Indian Institute of Technology',
            'branch': 'Computer Science',
            'year': '3',
            'semester': '6',
            'cgpa': '8.90',
            'target_role': 'Full Stack Developer',
            'preferred_domain': 'Web Development',
            'career_timeline': '6 months',
            'target_companies': 'Google, Microsoft, Stripe',
            'github_url': 'https://github.com/priyapatel',
            'linkedin_url': 'https://linkedin.com/in/priyapatel',
            'leetcode_url': 'https://leetcode.com/priyapatel',
            'skill_names': ['Python', 'React', 'SQL', 'Docker'],
            'skill_levels': ['advanced', 'intermediate', 'advanced', 'beginner'],
            'interest_names': ['Web Development', 'Cloud Computing', 'System Design']
        }, follow_redirects=True)

        self.assertEqual(edit_resp.status_code, 200)
        self.assertIn(b'profile has been saved successfully', edit_resp.data)
        self.assertIn(b'Indian Institute of Technology', edit_resp.data)
        self.assertIn(b'Full Stack Developer', edit_resp.data)
        self.assertIn(b'Python', edit_resp.data)
        self.assertIn(b'React', edit_resp.data)
        self.assertIn(b'Cloud Computing', edit_resp.data)

        # 4. Verify in database
        with self.app.app_context():
            db_user = User.query.filter_by(email='priya@eng.edu').first()
            self.assertEqual(db_user.profile.college, 'Indian Institute of Technology')
            self.assertEqual(float(db_user.profile.cgpa), 8.90)
            self.assertEqual(db_user.profile.target_role, 'Full Stack Developer')
            self.assertEqual(len(db_user.skills), 4)
            self.assertEqual(len(db_user.interests), 3)
            # Check completion score is 100% since all sections were populated
            self.assertEqual(db_user.profile.completion_percentage, 100)

    def test_completion_calculator_logic(self):
        """Test calculation logic across various profile states."""
        with self.app.app_context():
            user = User(name='Test User', email='test@calc.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.flush()

            # Empty profile
            empty_profile = Profile(user_id=user.id)
            score_empty = calculate_profile_completion(empty_profile, [], [])
            self.assertEqual(score_empty, 0)

            # Partially filled profile
            partial_profile = Profile(
                user_id=user.id,
                college='Engineering College',
                branch='IT',
                target_role='Backend Engineer'
            )
            # college(5) + branch(5) + target_role(10) = 20
            score_partial = calculate_profile_completion(partial_profile, [], [])
            self.assertEqual(score_partial, 20)

            # Profile with skills
            skills = [
                Skill(user_id=user.id, name='Python', level='advanced'),
                Skill(user_id=user.id, name='Django', level='intermediate'),
                Skill(user_id=user.id, name='PostgreSQL', level='intermediate')
            ]
            interests = [
                Interest(user_id=user.id, name='Backend Systems')
            ]
            # 20 + skills >= 1 (10) + skills >= 3 (10) + interests >= 1 (10) = 50
            score_with_skills = calculate_profile_completion(partial_profile, skills, interests)
            self.assertEqual(score_with_skills, 50)


if __name__ == '__main__':
    unittest.main()
