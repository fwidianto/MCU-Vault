"""
Authentication routes for user registration, login, and logout.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.utils.helpers import validate_email, validate_password

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page and handler."""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        # Validate input
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html')
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if user is None:
            # Also try email
            user = User.query.filter_by(email=username).first()
        
        # Check password
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to next page if specified
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page and handler."""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate input
        errors = []
        
        if not username:
            errors.append('Username is required.')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        elif len(username) > 80:
            errors.append('Username must not exceed 80 characters.')
        
        if not email:
            errors.append('Email is required.')
        elif not validate_email(email):
            errors.append('Please enter a valid email address.')
        
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            errors.append(error_msg)
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        # Check for existing user
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', 
                                   username=username, 
                                   email=email)
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))