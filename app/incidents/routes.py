from flask import Blueprint, render_template, request, redirect, session, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Incident
from datetime import datetime

incidents_bp = Blueprint("incidents", __name__, template_folder="../templates")

@incidents_bp.route("/list")
@login_required
def list_incidents():
    incidents = Incident.query.order_by(Incident.created_at.desc()).all()
    result = []
    for i in incidents:
        data = i.to_dict()
        data["idle_time"] = calculate_idle_time(i.reported_at)
        result.append(data)
    return jsonify(result)


@incidents_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_incident():
    if request.method == "POST":

        # Extract form data
        title = request.form.get("title")
        department = request.form.get("department")
        category = request.form.get("category")   # Falls, Cuts, Fires, etc.
        incident_type = request.form.get("type")  # Near-Miss, Incident, etc.
        severity = request.form.get("severity")
        description = request.form.get("description")

        # Date from form
        incident_datetime = request.form.get("incident_datetime")
        reported_at_form = request.form.get("reported_at")   # <--- ADD THIS FIELD (optional from UI)

        # Numeric fields
        employees = int(request.form.get("employees_affected", 0))
        hours_per_employee = float(request.form.get("hours_per_employee", 0))
        idle_time = float(request.form.get("idle_time_hours", 0))
        cost_per_hour = float(request.form.get("cost_per_hour", 0))

        # Auto calculations
        hours_lost = employees * hours_per_employee
        total_cost = hours_lost * cost_per_hour

        # Convert main incident date
        incident_dt = (
            datetime.strptime(incident_datetime, "%Y-%m-%d")
            if incident_datetime else datetime.utcnow()
        )

        # Convert reported_at
        reported_at = (
            datetime.strptime(reported_at_form, "%Y-%m-%dT%H:%M")
            if reported_at_form else datetime.utcnow()
        )

        # Create Incident
        inc = Incident(
            title=title,
            department=department,
            category=category,
            type=incident_type,
            severity=severity,
            description=description,
            incident_datetime=incident_dt,
            reported_at=reported_at,        # <-- ADDED HERE
            employees_affected=employees,
            hours_per_employee=hours_per_employee,
            idle_time_hours=idle_time,
            hours_lost=hours_lost,
            cost_per_hour=cost_per_hour,
            total_cost=total_cost,
            created_by=current_user,
        )

        db.session.add(inc)
        db.session.commit()

        flash("Incident created successfully!", "success")
        
        return redirect(url_for("incidents.list_incidents"))
        

    return render_template("new_incident.html")


@incidents_bp.route("/<int:incident_id>")
@login_required
def view_incident(incident_id):
    # Fetch incident directly from the database
    incident = Incident.query.get_or_404(incident_id)

    # Optionally calculate idle time
    idle_time = calculate_idle_time(incident.reported_at)

    # Pass the incident object directly to the template
    return render_template(
        "incident_detail.html",
        incident=incident,
        idle_time=idle_time
    )

@incidents_bp.route("/edit/<int:incident_id>", methods=["POST"])
@login_required
def edit_incident(incident_id):
    inc = Incident.query.get_or_404(incident_id)

    # Read updated form data from the incident detail page
    inc.title = request.form.get("title", inc.title)
    inc.department = request.form.get("department", inc.department)
    inc.category = request.form.get("category", inc.category)
    inc.type = request.form.get("type", inc.type)
    inc.severity = request.form.get("severity", inc.severity)
    inc.description = request.form.get("description", inc.description)

    # Main incident date
    incident_datetime = request.form.get("incident_datetime")
    if incident_datetime:
        try:
            inc.incident_datetime = datetime.strptime(incident_datetime, "%Y-%m-%d")
        except:
            pass

    # reported_at date (NEW)
    reported_at = request.form.get("reported_at")
    if reported_at:
        try:
            inc.reported_at = datetime.strptime(reported_at, "%Y-%m-%dT%H:%M")
        except:
            pass
    else:
        # Keep old value OR set automatically
        inc.reported_at = inc.reported_at or datetime.utcnow()

    # Numeric fields
    try:
        inc.employees_affected = int(request.form.get("employees_affected", inc.employees_affected))
        inc.hours_per_employee = float(request.form.get("hours_per_employee", inc.hours_per_employee))
        inc.idle_time_hours = float(request.form.get("idle_time_hours", inc.idle_time_hours))
        inc.cost_per_hour = float(request.form.get("cost_per_hour", inc.cost_per_hour))
    except:
        pass

    # Recalculate values
    inc.hours_lost = inc.employees_affected * inc.hours_per_employee
    inc.total_cost = inc.hours_lost * inc.cost_per_hour

    db.session.commit()
    flash("Incident updated successfully!", "success")
    

    return redirect(url_for("incidents.view_incident", incident_id=incident_id))


@incidents_bp.route("/<int:incident_id>/delete", methods=["POST"])
@login_required
def delete_incident(incident_id):
    inc = Incident.query.get_or_404(incident_id)
    db.session.delete(inc)
    db.session.commit()
    flash("Incident deleted successfully!", "success")
    return redirect(url_for("incidents.list_incidents"))
    


from datetime import datetime

def calculate_idle_time(reported_at):
    if not reported_at:
        return "Unknown"

    delta = datetime.utcnow() - reported_at
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    result = []
    if days: result.append(f"{days} days")
    if hours: result.append(f"{hours} hours")
    if minutes: result.append(f"{minutes} minutes")

    return ", ".join(result) or "0 minutes"

@incidents_bp.template_filter('idle_time')
def idle_time_filter(reported_at):
    return calculate_idle_time(reported_at)