from flask import Blueprint, get_flashed_messages, render_template, redirect, session, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from .. import db, mail
from ..models import User, Role
from .forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm
from functools import wraps

# Create the auth blueprint - THIS LINE MUST EXIST
bp = Blueprint('auth', __name__)

def roles_required(*roles):
    """Allow only users with given roles."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                flash("You are not authorized to access this page.", "danger")
                return redirect(url_for("main.index"))
            return f(*args, **kwargs)
        return wrapper
    return decorator

def load_user(user_id):
    return User.query.get(int(user_id))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    # Clear any leftover flash messages
    get_flashed_messages()

    # Redirect already logged-in users to dashboard
    if current_user.is_authenticated:
        logout_user()  # force logout
        return redirect(url_for('auth.login'))

    form = RegisterForm()
    if form.validate_on_submit():
        # Check if email is already registered
        existing_user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if existing_user:
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        # Create new user (do NOT log them in yet)
        user = User(
            full_name=form.full_name.data,
            email=form.email.data.strip().lower()
        )
        user.set_password(form.password.data)

        # Assign default role
        employee_role = Role.query.filter_by(name="Employee").first()
        if employee_role:
            user.roles.append(employee_role)

        # Save user to database
        db.session.add(user)
        db.session.commit()

        # Generate email confirmation token
        token = user.get_token(purpose='confirm')
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)

        # Send confirmation email
        msg = Message('Confirm your account', recipients=[user.email])
        msg.body = f'Please confirm your account by clicking the link: {confirm_url}'
        mail.send(msg)

        # Flash success message and redirect to login
        flash('Registration successful! Check your email to confirm your account.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@bp.route('/confirm/<token>')
def confirm_email(token):
    user = User.verify_token(token, purpose='confirm')
    if not user:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))
        

    
    if user.is_active:
        flash('Account already confirmed. Please log in.', 'info')
        
    else:
        user.is_active = True
        db.session.commit()
        flash('Your account has been confirmed! You can now log in.', 'success')
        
    return redirect(url_for('auth.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any leftover flash messages
    get_flashed_messages()
    
    # If user is already logged in → go to login page (force re-login)
    if current_user.is_authenticated:
        logout_user()  # force logout
        return redirect(url_for('auth.login'))

    form = LoginForm()

    if form.validate_on_submit():
        # Form was submitted and passed validation
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()

        # Check user exists + password correct + account active
        if not user or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))
            
        if not user.is_active:
            flash('Your account is not activated. Please check your email to confirm your account.', 'warning')
            return redirect(url_for('auth.login'))
        

        # SUCCESS → log the user in
        login_user(user, remember=False)
        session.permanent = True  # enables timeout
        flash('Login successful!', 'success')
    

        # Redirect based on role (adjust these endpoints to what you actually have)
        if user.role == "admin":
            next_page = url_for('admin.admin_dashboard')  # or whatever your admin route is
        elif user.role == "auditor":
            next_page = url_for('auditor.auditor_dashboard')
        else:
            next_page = url_for('main.dashboard')

        # Respect the ?next= parameter if it's safe
        next_url = request.args.get('next')
        if next_url and next_url.startswith('/'):
            next_page = next_url

        return redirect(next_page)

    # GET request or form didn't validate → show login page
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))
    


@bp.route('/reset_password_request', methods=['GET','POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_token(purpose='reset')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            msg = Message('Password Reset', recipients=[user.email])
            msg.body = f'Reset your password: {reset_url}'
            mail.send(msg)
        
        flash('If an account with that email exists, we sent a reset email.', 'info')
        return redirect(url_for('auth.login'))
        

    
    return render_template('auth/reset_request.html', form=form)

@bp.route('/reset_password/<token>', methods=['GET','POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    user = User.verify_token(token, purpose='reset')
    if not user:
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('auth.login'))
        
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset. You can now log in.', 'success')
        
        return redirect(url_for('auth.login'))
        
    
    return render_template('auth/reset_password.html', form=form)