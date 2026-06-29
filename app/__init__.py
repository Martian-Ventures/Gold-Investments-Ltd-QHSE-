import os
from flask import Flask, url_for, redirect
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_mail import Mail
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from flask_apscheduler import APScheduler

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
mail = Mail()
scheduler = APScheduler()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") or app.config.get("SECRET_KEY") or "dev-secret"
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['REMEMBER_COOKIE_DURATION'] = 3600
    app.config['SESSION_PROTECTION'] = 'basic'
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)

    login.login_message_category = "info"

    from app.models import User, Incident, IncidentUpdate

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    jwt = JWTManager(app)

    # Blueprints
    from app.auth.routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .main.routes import bp as main_bp
    app.register_blueprint(main_bp)

    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Register incidents blueprint
    from app.incidents.routes import incidents_bp
    app.register_blueprint(incidents_bp, url_prefix='/incidents')

    # Root redirect
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('main.dashboard'))
        return redirect(url_for('auth.register'))

    # Initialize scheduler — disabled on serverless environments (Vercel)
    # APScheduler requires a persistent process; skip it if running serverless
    if not os.getenv('VERCEL'):
        scheduler.init_app(app)
        scheduler.start()

    return app

if __name__ == "__main__":
    create_app().run(debug=True)
