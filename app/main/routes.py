from flask import Blueprint, app, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user
from app import db
from app.models import User, Incident
from app.decorators import role_required
from datetime import datetime
from ..auth.forms import RegisterForm

bp = Blueprint('main', __name__)
#incidents_bp = Blueprint("incidents", __name__, template_folder="templates")
#admin_bp = Blueprint("admin", __name__, template_folder="templates")

@bp.route('/')
def index():
    form = RegisterForm()
    return render_template('auth/register.html', form=form)
  # or redirect to /auth/login

@bp.route('/dashboard')
@login_required
@login_required
def dashboard():
   # Serve different templates by role
    if current_user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    elif current_user.role == 'auditor':
        return render_template('auditor/dashboard.html', user=current_user)
    else:  # employee/user
        return render_template('index.html', user=current_user)
    

@bp.route('/admin')
@login_required
@role_required('Admin')
def admin_dashboard():
    return render_template('admin/admin_dashboard.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # handle form submission, e.g., create user
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.register'))
        

    return render_template('auth/register.html', form=form)

