import os
from flask import Flask, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_mail import Mail
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from flask_apscheduler import APScheduler

# Import config and get_config function
from .config import Config, get_config

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
mail = Mail()
scheduler = APScheduler()

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        # Determine which config to use based on environment
        env = os.environ.get('FLASK_ENV', 'development')
        config_class = get_config(env)
    
    app.config.from_object(config_class)
    
    # Override database URI for Vercel if needed
    if os.environ.get('VERCEL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"postgresql://{os.environ.get('PGUSER')}:{os.environ.get('PGPASSWORD')}"
            f"@{os.environ.get('PGHOST')}:{os.environ.get('PGPORT')}/{os.environ.get('PGDATABASE')}"
        )
    else:
    # FORCE 5433 LOCALLY: Ignore the machine's broken default environment variable
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost:5433/qhse_db'
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    
    login.login_message_category = "info"
    
    # JWT Manager
    jwt = JWTManager(app)
    
    # User loader
    from app.models import User
    
    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    # Register Blueprints
    from app.auth.routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main.routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.incidents.routes import incidents_bp
    app.register_blueprint(incidents_bp, url_prefix='/incidents')
    
    # Root redirect
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('main.dashboard'))
        return redirect(url_for('auth.register'))
    
    # Initialize scheduler - disabled on serverless environments
    if not os.getenv('VERCEL') and not os.getenv('AWS_LAMBDA'):
        try:
            scheduler.init_app(app)
            scheduler.start()
        except Exception as e:
            app.logger.warning(f"Scheduler could not be started: {e}")
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)