from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from flask_login import current_user, login_required
from app import db
from app.auth.routes import roles_required
from app.models import User, Role
from app.decorators import role_required
from app.models import Audit

admin_bp = Blueprint("admin", __name__, template_folder="../templates")

@admin_bp.route("/")
@login_required
@roles_required("admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")

# List users and manage roles
@admin_bp.route("/users")
@login_required
@roles_required("admin")
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_users.html", users=users)

@admin_bp.route("/users")
@login_required
@roles_required("admin")
def manage_users():
    users = User.query.all()
    roles = Role.query.all()
    return render_template("admin_users.html", users=users, roles=roles)

# Create user (POST form)
@admin_bp.route("/users/create", methods=["GET","POST"])
@login_required
@roles_required("admin")
def create_user():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        role = request.form.get("role")
        password = request.form.get("password")
        if User.query.filter_by(email=email).first():
            flash("Email already exists", "danger")
            return redirect(url_for("admin.create_user"))
            

        u = User(email=email, role=role)
        u.set_password(password or "ChangeMe123!")
        db.session.add(u)
        db.session.commit()
        db.session.add(Audit(actor_id=current_user.id, actor_email=current_user.email, action="create_user", target=email, detail=f"role={role}"))
        db.session.commit()
        flash("User created", "success")
        return redirect(url_for("admin.list_users"))
        

    return render_template("admin_user_create.html")

# Edit user (role or password)
@admin_bp.route("/users/<int:user_id>/edit", methods=["GET","POST"])
@login_required
@roles_required("admin")
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        new_role = request.form.get("role")
        new_password = request.form.get("password")
        old_role = user.role
        user.role = new_role
        if new_password:
            user.set_password(new_password)
        db.session.commit()
        db.session.add(Audit(actor_id=current_user.id, actor_email=current_user.email, action="edit_user", target=user.email, detail=f"{old_role}=>{new_role}"))
        db.session.commit()
        flash("User updated", "success")
        
        return redirect(url_for("admin.list_users"))
    return render_template("admin_user_edit.html", user=user)

# Delete user
@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    db.session.add(Audit(actor_id=current_user.id, actor_email=current_user.email, action="delete_user", target=user.email))
    db.session.commit()
    flash("User deleted", "success")
    return redirect(url_for("admin.list_users"))
    


@admin_bp.route("/users/<int:user_id>/assign", methods=["POST"])
@role_required("Admin")
def assign_role(user_id):
    user = User.query.get_or_404(user_id)
    role_id = request.form.get("role_id")
    role = Role.query.get(role_id)
    if role and role not in user.roles:
        user.roles.append(role)
        db.session.commit()
        flash(f"Assigned role {role.name} to {user.full_name}", "success")
        
    return redirect(url_for("admin.manage_users"))
