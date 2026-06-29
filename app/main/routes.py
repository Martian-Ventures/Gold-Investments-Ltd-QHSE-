from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import User, Incident
from app.decorators import role_required
from datetime import datetime
from ..auth.forms import RegisterForm

bp = Blueprint('main', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return render_template('admin/admin_dashboard.html', user=current_user)
    elif current_user.role == 'auditor':
        # auditor gets the same dashboard as employee for now
        return render_template('index.html', user=current_user)
    else:
        return render_template('index.html', user=current_user)
