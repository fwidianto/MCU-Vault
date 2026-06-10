"""
MCU Vault Flask Application Factory.
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name='default'):
    """
    Application factory for creating Flask app instances.
    
    Args:
        config_name: Configuration to use (default, development, production)
    
    Returns:
        Flask application instance
    """
    # Get the project root (parent of app directory) for templates and static
    import app as app_module
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(app_module.__file__)))
    
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static')
    )
    
    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])

    # Dynamically set SESSION_COOKIE_SECURE based on HTTPS detection
    # This allows production to work over HTTP when behind a proxy without HTTPS
    if config_name == 'production':
        is_https = (
            app.config.get('SECURE_COOKIE_HTTPS', False) or
            os.environ.get('HTTPS', '').lower() in ('on', '1') or
            os.environ.get('FLASK_HTTPS', '').lower() == 'true'
        )
        app.config['SESSION_COOKIE_SECURE'] = is_https

    # Ensure upload directory exists
    upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Initialize CSRF protection (skip for API-only endpoints)
    csrf.init_app(app)
    
    # User loader for Flask-Login
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.records import records_bp
    from app.routes.upload import upload_bp
    from app.routes.analytics import analytics_bp
    from app.routes.ocr import ocr_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(ocr_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app