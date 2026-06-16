# fill_reported_at.py
from app import app, db
from app.models import Incident
from datetime import datetime

with app.app_context():
    incidents = Incident.query.filter(Incident.reported_at.is_(None)).all()
    print(f"Found {len(incidents)} incidents with missing reported_at.")

    for inc in incidents:
        inc.reported_at = inc.created_at or datetime.utcnow()

    db.session.commit()
    print("reported_at fields updated successfully.")
