# run.py
import os
from app import create_app, db
from app.models import User

app = create_app()

# Only run DB setup when running locally (not on Vercel serverless)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email="admin@example.com").first():
            admin = User(
                full_name="Administrator",
                email="admin@example.com",
                role="admin",
                is_active=True
            )
            admin.set_password("AdminPass123!")
            db.session.add(admin)
            db.session.commit()
            print("Created default admin → email: admin@example.com / password: AdminPass123!")
        else:
            print("Admin user already exists.")

    app.run(debug=True)
