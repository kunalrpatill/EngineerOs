"""
Authentication Blueprint for EngineerOS.
Handles student registration, login, and logout with session management.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlsplit
from app.extensions import db
from app.models.user import User
from app.models.profile import Profile
from app.forms.auth_forms import LoginForm, RegisterForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle new student account registration.
    Renders registration form and creates new User and initial Profile on submission.
    """
    # If user is already logged in, redirect them to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegisterForm()

    if form.validate_on_submit():
        try:
            # 1. Create the new User object with hashed password
            new_user = User(
                name=form.name.data.strip(),
                email=form.email.data.strip().lower()
            )
            new_user.set_password(form.password.data)

            # 2. Add user to database session
            db.session.add(new_user)
            db.session.flush()  # Populates new_user.id before committing

            # 3. Create a blank associated profile for the new student
            initial_profile = Profile(
                user_id=new_user.id,
                completion_percentage=0
            )
            db.session.add(initial_profile)

            # 4. Commit transaction
            db.session.commit()

            flash('Registration successful! Welcome to EngineerOS. Please sign in to continue.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'danger')

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle student login with session management via Flask-Login.
    """
    # If user is already logged in, redirect them to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()

        # Verify user existence and password correctness
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash(f'Welcome back, {user.name}!', 'success')

            # Handle safe redirection if user was intercepted on a protected route
            next_page = request.args.get('next')
            if not next_page or urlsplit(next_page).netloc != '':
                next_page = url_for('dashboard.index')

            return redirect(next_page)
        else:
            flash('Invalid email or password. Please check your credentials and try again.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """
    Log out the current student and clear their session.
    """
    logout_user()
    flash('You have been signed out successfully.', 'info')
    return redirect(url_for('main.home'))
