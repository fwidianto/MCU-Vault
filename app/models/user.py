"""
User model for authentication.
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    """
    User model for storing user account information.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to MCU records
    mcu_records = db.relationship('MCURecord', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """
        Hash and set the user's password.
        
        Args:
            password: Plain text password
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Verify the user's password.
        
        Args:
            password: Plain text password to verify
        
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def total_records(self):
        """Get total number of MCU records for this user."""
        return self.mcu_records.count()
    
    @property
    def latest_record(self):
        """Get the most recent MCU record for this user."""
        return self.mcu_records.order_by(MCURecord.created_at.desc()).first()