"""
MCU Record and Uploaded File models.
"""
from datetime import datetime
from app import db


class MCURecord(db.Model):
    """
    MCU Record model for storing medical check-up information.
    """
    __tablename__ = 'mcu_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(200), nullable=False, index=True)
    company = db.Column(db.String(200), index=True)
    mcu_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, cleared, not-cleared, needs-follow-up
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to uploaded files
    files = db.relationship('UploadedFile', backref='mcu_record', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<MCURecord {self.patient_name} - {self.mcu_date}>'
    
    @property
    def total_files(self):
        """Get total number of uploaded files."""
        return self.files.count()
    
    @property
    def status_badge_class(self):
        """Get Bootstrap badge class based on status."""
        status_classes = {
            'pending': 'bg-warning',
            'cleared': 'bg-success',
            'not-cleared': 'bg-danger',
            'needs-follow-up': 'bg-info'
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def to_dict(self):
        """Convert record to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'patient_name': self.patient_name,
            'company': self.company,
            'mcu_date': self.mcu_date.isoformat() if self.mcu_date else None,
            'status': self.status,
            'notes': self.notes,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'total_files': self.total_files
        }


class UploadedFile(db.Model):
    """
    Uploaded File model for storing file metadata.
    """
    __tablename__ = 'uploaded_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # pdf, image
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    mime_type = db.Column(db.String(100))
    mcu_record_id = db.Column(db.Integer, db.ForeignKey('mcu_records.id'), nullable=False, index=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UploadedFile {self.original_filename}>'
    
    @property
    def file_extension(self):
        """Get file extension from original filename."""
        if '.' in self.original_filename:
            return self.original_filename.rsplit('.', 1)[1].lower()
        return ''
    
    @property
    def is_pdf(self):
        """Check if file is a PDF."""
        return self.file_type == 'pdf'
    
    @property
    def is_image(self):
        """Check if file is an image."""
        return self.file_type in ['jpg', 'jpeg', 'png']
    
    @property
    def file_size_formatted(self):
        """Get human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def to_dict(self):
        """Convert file to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'mcu_record_id': self.mcu_record_id,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }