from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import login
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from datetime import datetime


user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), unique=True,  nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.Enum("admin", "auditor", "employee", name="role_enum"), nullable=False, default="employee")
    roles = db.relationship("Role", secondary=user_roles, backref=db.backref("users", lazy="dynamic"))
    is_active = db.Column(db.Boolean, default=True)     # email confirmed
    twofa_secret = db.Column(db.String(32), nullable=True) # optional TOTP secret

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_token(self, expires_sec=3600, purpose='confirm'):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id, 'purpose': purpose})
    
    def has_role(self, role_name):
        return any(r.name == role_name for r in self.roles)

    def __repr__(self):
        return f"<User {self.full_name} - {self.email}>"
    
    def get_id(self):
        return str(self.id)  # Ensure this returns a string

    @staticmethod
    def verify_token(token, max_age=3600, purpose='confirm'):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=max_age)
        except Exception:
            return None
        if data.get('purpose') != purpose:
            return None
        return User.query.get(data.get('user_id'))
    
    # relationships
    incidents = db.relationship(
        "Incident",
        back_populates="created_by",
        overlaps="assigned_incidents,investigator"
    )
    assigned_incidents = db.relationship(
        "Incident",
        back_populates="investigator",
        overlaps="incidents,created_by"
    )



class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Role {self.name}>"
    
class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)

    # Basic fields
    title = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(128))  # Admin, Production, Finance, Logistics, QC, etc.
    category = db.Column(db.String(64))  # Falls, Cuts, Burns, Fires, etc.
    type = db.Column(db.String(64))  # Near-Miss, Incident, etc.
    severity = db.Column(db.String(32))
    description = db.Column(db.Text)

    # New fields
    employees_affected = db.Column(db.Integer, nullable=False, default=0)
    hours_per_employee = db.Column(db.Float, nullable=False, default=0.0)  # used for man-hours
    idle_time_hours = db.Column(db.Float, nullable=False, default=0.0)  # idle time since incident
    hours_lost = db.Column(db.Float, nullable=False, default=0.0)
    cost_per_hour = db.Column(db.Float, nullable=False, default=0.0)
    total_cost = db.Column(db.Float, nullable=False, default=0.0)
    investigator_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    investigator = db.relationship(
        "User",
        back_populates="assigned_incidents",
        overlaps="incidents,created_by"
    )

    # Date & user tracking
    incident_datetime = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_by = db.relationship(
        "User",
        back_populates="incidents",
        overlaps="assigned_incidents,investigator"
    )

    status = db.Column(db.String(32), default="Reported")
    # Reported, Under Investigation, Resolved, Closed

    # Auto calculation before saving
    def calculate_totals(self):
        self.hours_lost = self.employees_affected * self.hours_per_employee
        self.total_cost = self.hours_lost * self.cost_per_hour

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "department": self.department,
            "category": self.category,
            "type": self.type,
            "severity": self.severity,
            "description": self.description,
            "employees_affected": self.employees_affected,
            "hours_per_employee": self.hours_per_employee,
            "idle_time_hours": self.idle_time_hours,
            "hours_lost": self.hours_lost,
            "cost_per_hour": self.cost_per_hour,
            "total_cost": self.total_cost,
            "incident_datetime": self.incident_datetime.isoformat() if self.incident_datetime else None,
            "status": self.status,
            "created_by": self.created_by.username if self.created_by else None,
            "created_at": self.created_at.isoformat(),
        }
    
        
    @property
    def idle_timedelta(self):
        # returns a datetime.timedelta
        reported = self.reported_at or datetime.utcnow()
        return datetime.utcnow() - reported

    @property
    def idle_hours(self):
        td = self.idle_timedelta
        return round(td.total_seconds() / 3600, 2)

    @property
    def idle_days(self):
        td = self.idle_timedelta
        return td.days + td.seconds / 86400

    @property
    def idle_human(self):
        td = self.idle_timedelta
        seconds = td.total_seconds()
        if seconds < 60:
            return f"{int(seconds)} seconds"
        if seconds < 3600:
            return f"{int(seconds // 60)} minutes"
        if seconds < 86400:
            return f"{round(seconds / 3600, 1)} hours"
        days = int(seconds // 86400)
        return f"{days} days"
    
        
class IncidentUpdate(db.Model):
    __tablename__ = "incident_updates"
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"))
    incident = db.relationship("Incident", backref=db.backref("updates", lazy=True))
    update_text = db.Column(db.Text, nullable=False)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    updated_by = db.relationship("User", backref=db.backref("incident_updates", lazy=True))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self):
        return f"<IncidentUpdate {self.id} for Incident {self.incident_id}>"
    
class Capa(db.Model):
    __tablename__ = "capas"
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=True)
    incident = db.relationship("Incident", backref=db.backref("capas", lazy=True))
    action = db.Column(db.String(500))
    owner = db.Column(db.String(255))
    due_date = db.Column(db.Date)
    status = db.Column(db.String(64), default="Open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Document(db.Model):
    __tablename__ = "documents"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    filename = db.Column(db.String(255))
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    uploaded_by = db.relationship("User")
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Audit(db.Model):
    __tablename__ = "audits"
    id = db.Column(db.Integer, primary_key=True)
    organization = db.Column(db.String(255))
    standard = db.Column(db.String(255))
    plan_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
@login.user_loader
def load_user(user_id):
    print(f"🔍 Loading user with ID: {user_id}")  # Debug
    return User.query.get(int(user_id))
    print(f"🔍 User loaded: {user}")  # Debug
    return user



