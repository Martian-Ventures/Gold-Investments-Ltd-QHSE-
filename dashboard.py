from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.auth.routes import roles_required
from app.models import AuditLog

dashboard_bp = Blueprint("dashboard", __name__, template_folder="templates")

@dashboard_bp.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return render_template("admin_dashboard.html")
        if current_user.role == "auditor":
            return render_template("auditor_dashboard.html")
        return render_template("user_dashboard.html")
    return render_template("index.html")

@dashboard_bp.route("/admin/dashboard")
@login_required
@roles_required("admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")

@dashboard_bp.route("/auditor/dashboard")
@login_required
@roles_required("auditor", "admin")
def auditor_dashboard():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(500).all()
    return render_template("auditor_logs.html", logs=logs)

@dashboard_bp.route("/user/dashboard")
@login_required
@roles_required("user","admin","auditor")
def user_dashboard():
    return render_template("user_dashboard.html")

@dashboard_bp.route("/about")
def about():
    return render_template("about.html")