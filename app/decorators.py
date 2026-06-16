# decorators.py
from functools import wraps
from flask import abort
from flask_login import current_user, login_required
from flask import redirect, url_for, flash   # ✅ import these

def role_required(*roles):
    """
    Restrict access to routes based on user roles.

    Usage:
        @app.route('/admin')
        @role_required('Admin')
        def admin_dashboard():
            return render_template('admin.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in
            if not current_user.is_authenticated:
                flash("You must be logged in to access this page.", "warning")
                return redirect(url_for('auth.login'))

            # Check if user role is allowed
            if current_user.role not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('main.index'))
                


            # Otherwise, proceed
            return f(*args, **kwargs)
        return decorated_function
    return decorator

#def role_required(*roles):
#    def wrapper(fn):
#        @wraps(fn)
#        @login_required
#        def decorated_view(*args, **kwargs):
#            if not current_user.is_authenticated:
#                return abort(401)
#            for r in roles:
#                if current_user.has_role(r):
#                    return fn(*args, **kwargs)
#            return abort(403)
#        return decorated_view
#    return wrapper
