# bootstrap_roles.py
from app import create_app, db
from app.models import Role, User   # ✅ make sure to import from app.models, not just models

app = create_app()

with app.app_context():
    roles = [
        ("Admin", "Full system control"),
        ("HSE Officer", "Handles incident entries & investigations"),
        ("Employee", "Submit/view incidents"),
        ("Auditor", "Read-only access to reports")
    ]

    for name, desc in roles:
        if not Role.query.filter_by(name=name).first():
            r = Role(name=name, description=desc)
            db.session.add(r)
    db.session.commit()

    # Optional: create default admin
    if not User.query.filter_by(username="admin").first():
        u = User(username="admin", email="admin@example.com")
        u.set_password("ChangeMe123!")  # make sure set_password exists in User model
        admin_role = Role.query.filter_by(name="Admin").first()
        u.roles.append(admin_role)
        db.session.add(u)
        db.session.commit()

    print("✅ Roles and default admin created successfully.")
