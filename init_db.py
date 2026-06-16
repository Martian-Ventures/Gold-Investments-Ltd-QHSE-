#!/usr/bin/env python
"""Initialize the database with tables and default admin user."""

from app import create_app, db
from app.models import User
import os

# Set migration environment to skip scheduler
os.environ['FLASK_ENV'] = 'migration'

app = create_app()

with app.app_context():
    print("Creating database tables...")
    try:
        # Create all tables (skip drop to avoid table existence checks)
        db.create_all()
        print("✓ Created all tables successfully")
        
        # Create default admin user
        try:
            existing = User.query.filter_by(email="admin@example.com").first()
            if existing:
                print("⚠ Admin user already exists, skipping creation")
            else:
                admin = User(
                    full_name="Administrator",
                    email="admin@example.com",
                    role="admin",
                    is_active=True
                )
                admin.set_password("AdminPass123!")
                db.session.add(admin)
                db.session.commit()
                print("✓ Created default admin user (admin@example.com / AdminPass123!)")
        except Exception as e:
            print(f"⚠ Warning creating admin user: {e}")
            db.session.rollback()
        
        print("\n✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.session.rollback()
        raise
