"""
Routes package for MCU Vault.
"""
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.records import records_bp
from app.routes.upload import upload_bp
from app.routes.analytics import analytics_bp

__all__ = ['auth_bp', 'dashboard_bp', 'records_bp', 'upload_bp', 'analytics_bp']