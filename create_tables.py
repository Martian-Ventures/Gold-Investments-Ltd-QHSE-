#!/usr/bin/env python
from app import create_app, db
from app.models import User, Incident, Role, Capa, Document, Audit, AdminLog, IncidentUpdate

app = create_app()

def create_all_tables():
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("✅ Tables created successfully!")
            
            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"\n📊 Tables created ({len(tables)}):")
            for table in sorted(tables):
                print(f"  - {table}")
            
            # Create default roles if they don't exist
            print("\nCreating default roles...")
            roles = ['admin', 'auditor', 'employee']
            for role_name in roles:
                if not Role.query.filter_by(name=role_name).first():
                    role = Role(name=role_name, description=f'{role_name.capitalize()} role')
                    db.session.add(role)
                    print(f"  Created role: {role_name}")
            db.session.commit()
            print("✅ Default roles created!")
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    create_all_tables()