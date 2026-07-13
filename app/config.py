from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    
    # PostgreSQL Database Configuration
    # Priority: Vercel Env Vars → DATABASE_URL → Local PostgreSQL
    if os.environ.get('VERCEL'):
        # Vercel Postgres (production)
        raw_url = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
        if raw_url and raw_url.startswith("postgres://"):
            raw_url = raw_url.replace("postgres://", "postgresql://", 1)
    else:
        # Use DATABASE_URL if provided, otherwise fallback to local PostgreSQL
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            'DATABASE_URL', 
            'postgresql://neondb_owner:npg_08JdFQcqtzEu@ep-floral-sunset-atna7psk-pooler.c-9.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require'  # Default local PostgreSQL
        )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['1', 'true', 'yes']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # JWT Configuration (if using Flask-JWT-Extended)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Security
    SESSION_PROTECTION = 'basic'
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'false').lower() in ['1', 'true', 'yes']
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'
    
    # Use local PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://neondb_owner:npg_08JdFQcqtzEu@ep-floral-sunset-atna7psk-pooler.c-9.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require'
    )
    SQLALCHEMY_ECHO = True  # Log SQL queries

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'
    
    # Force HTTPS in production
    PREFERRED_URL_SCHEME = 'https'
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    
    # Production database should come from environment variables
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    """Testing configuration running against local PostgreSQL"""
    TESTING = True
    DEBUG = True
    ENV = 'testing'
    
    # Switch from SQLite to your active local PostgreSQL instance
    SQLALCHEMY_DATABASE_URI = 'postgresql://neondb_owner:npg_08JdFQcqtzEu@ep-floral-sunset-atna7psk-pooler.c-9.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require'
    
    # Disable CSRF tokens during testing so your API/Form tests can submit requests smoothly
    WTF_CSRF_ENABLED = False

# Configuration dictionary for easy switching
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Helper function to get config by name
def get_config(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    return config.get(config_name, DevelopmentConfig)
