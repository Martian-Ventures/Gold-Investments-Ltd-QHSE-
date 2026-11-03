from flask import Blueprint, current_app, get_flashed_messages, jsonify, render_template, redirect, session, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import BadRequest
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
    is_json_request = request.is_json

    # Redirect already logged-in users to dashboard
    if current_user.is_authenticated:
        logout_user()  # force logout
        return redirect(url_for('auth.login'))

    if is_json_request:
        try:
            payload = request.get_json()
        except BadRequest:
            return jsonify(error='Request body must contain valid JSON.'), 400
        if not isinstance(payload, dict):
            return jsonify(error='Request body must be a JSON object.'), 400
        form_fields = ('full_name', 'email', 'password', 'password2', 'role')
        if any(key in payload and not isinstance(payload[key], str) for key in form_fields):
            return jsonify(error='Registration fields must be strings.'), 400
        form = RegisterForm(formdata=MultiDict(payload), meta={'csrf': False})
    else:
        form = RegisterForm()

    if form.validate_on_submit():
        try:
            email = form.email.data.strip().lower()
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                if is_json_request:
                    return jsonify(error='Email already registered.'), 409
                flash('Email already registered. Please log in.', 'warning')
                return redirect(url_for('auth.login'))

            user = User(full_name=form.full_name.data.strip(), email=email, is_active=False)
            user.set_password(form.password.data)

            employee_role = Role.query.filter_by(name="Employee").first()
            if employee_role:
                user.roles.append(employee_role)

            db.session.add(user)
            db.session.flush()
            token = user.get_token(purpose='confirm')
            confirm_url = url_for('auth.confirm_email', token=token, _external=True)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            current_app.logger.info("Registration rejected because a unique user field already exists.")
            if is_json_request:
                return jsonify(error='An account with these details already exists.'), 409
            flash('An account with these details already exists.', 'warning')
            return render_template('auth/register.html', form=form), 409
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("Database error during user registration.")
            if is_json_request:
                return jsonify(error='Registration could not be completed. Please try again later.'), 500
            flash('Registration could not be completed. Please try again later.', 'danger')
            return render_template('auth/register.html', form=form), 500
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Unexpected error during user registration.")
            if is_json_request:
                return jsonify(error='Registration could not be completed. Please try again later.'), 500
            flash('Registration could not be completed. Please try again later.', 'danger')
            return render_template('auth/register.html', form=form), 500

        email_sent = True
        try:
            msg = Message('Confirm your account', recipients=[user.email])
            msg.body = f'Please confirm your account by clicking the link: {confirm_url}'
            mail.send(msg)
        except Exception:
            email_sent = False
            current_app.logger.exception("Failed to send the registration confirmation email.")

        message = (
            'Registration successful! Check your email to confirm your account.'
            if email_sent else
            'Registration was created, but the confirmation email could not be sent. Please contact support.'
        )
        if is_json_request:
            return jsonify(message=message), 201
        flash(message, 'success' if email_sent else 'warning')
        return redirect(url_for('auth.login'))

    if is_json_request:
        return jsonify(error='Please correct the registration details.', fields=form.errors), 400
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
    

        # Redirect based on role
        if user.role == "admin":
            next_page = url_for('main.dashboard')
        elif user.role == "auditor":
            next_page = url_for('main.dashboard')
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
            try:
                msg = Message('Password Reset', recipients=[user.email])
                msg.body = f'Reset your password: {reset_url}'
                mail.send(msg)
            except Exception as e:
                # Fallback for development
                print(f"\n📧 [DEVELOPMENT MODE] Reset email could not be sent: {e}")
                print(f"🔗 Reset Link: {reset_url}\n")
                flash(f'If an account with that email exists, we sent a reset email. (Development Mode: Link printed to console: {reset_url})', 'info')
                return redirect(url_for('auth.login'))
        
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