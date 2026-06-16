# run.py
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()  # Create tables if they don't exist

    # Create default admin user if not already present
    if not User.query.filter_by(email="admin@example.com").first():
        admin = User(
            full_name="Administrator",     # required field
            email="admin@example.com",
            role="admin",
            is_active=True
        )
        admin.set_password("AdminPass123!")   # this line was missing the object!
        db.session.add(admin)
        db.session.commit()
        print("Created default admin → email: admin@example.com / password: AdminPass123!")
    else:
        print("Admin user already exists.")

if __name__ == '__main__':
    app.run(debug=True)