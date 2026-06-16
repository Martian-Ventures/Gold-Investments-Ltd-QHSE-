# scheduler.py

from datetime import datetime, timedelta
from flask_apscheduler import APScheduler
from flask_mail import Message

from app import app
from app.models import Audit, User
from flask_mail import Mail  # make sure mail = Mail(app) is here
from extensions import mail

scheduler = APScheduler()


# ---------- AUDIT SCHEDULING & NOTIFICATIONS ----------
@scheduler.task('interval', id='audit_check', seconds=60*60)  # every hour
def check_audits():
    with app.app_context():
        now = datetime.utcnow()
        soon = now + timedelta(days=3)

        audits = Audit.query.filter(
            Audit.is_completed == False,
            Audit.due_date <= soon
        ).all()

        for a in audits:
            auditors = User.query.filter_by(role='auditor').all()

            for aud in auditors:
                try:
                    msg = Message(
                        subject=f"Audit Due: Incident {a.incident_id}",
                        recipients=[aud.email],
                        body=f"""
Hello {aud.name},

This is a reminder that an audit is due:

Audit ID: {a.id}
Type: {a.audit_type}
Incident: {a.incident.title}
Due Date: {a.due_date} UTC

Regards,
Incident Management System
                        """
                    )
                    mail.send(msg)

                except Exception as e:
                    print("Mail send failed:", e)
