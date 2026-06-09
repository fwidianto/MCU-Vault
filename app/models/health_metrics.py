"""
HealthMetrics model for storing structured medical check-up health data.
"""
from datetime import datetime
from app import db


class HealthMetrics(db.Model):
    """
    Health Metrics model for storing structured health measurements.
    One-to-one relationship with MCURecord.
    """
    __tablename__ = 'health_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    mcu_record_id = db.Column(db.Integer, db.ForeignKey('mcu_records.id'), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Basic Measurements
    height_cm = db.Column(db.Float, nullable=True)  # Range: 50-250
    weight_kg = db.Column(db.Float, nullable=True)  # Range: 1-500
    bmi = db.Column(db.Float, nullable=True)  # Range: 5-100 (auto-calculated or manual)
    
    # Vital Signs
    systolic_bp = db.Column(db.Integer, nullable=True)  # Positive values only
    diastolic_bp = db.Column(db.Integer, nullable=True)  # Positive values only
    heart_rate = db.Column(db.Integer, nullable=True)  # Positive values only
    
    # Blood Sugar
    fasting_glucose = db.Column(db.Float, nullable=True)  # mg/dL
    hba1c = db.Column(db.Float, nullable=True)  # Percentage
    
    # Lipid Profile
    total_cholesterol = db.Column(db.Float, nullable=True)  # mg/dL
    ldl = db.Column(db.Float, nullable=True)  # mg/dL (bad cholesterol)
    hdl = db.Column(db.Float, nullable=True)  # mg/dL (good cholesterol)
    triglycerides = db.Column(db.Float, nullable=True)  # mg/dL
    
    # Liver Function
    sgot = db.Column(db.Float, nullable=True)  # SGOT/AST (U/L)
    sgpt = db.Column(db.Float, nullable=True)  # SGPT/ALT (U/L)
    
    # Kidney Function
    creatinine = db.Column(db.Float, nullable=True)  # mg/dL
    uric_acid = db.Column(db.Float, nullable=True)  # mg/dL
    
    # Additional Notes
    doctor_notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<HealthMetrics for MCURecord {self.mcu_record_id}>'
    
    def calculate_bmi(self):
        """Calculate BMI from height and weight."""
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            height_m = self.height_cm / 100
            self.bmi = round(self.weight_kg / (height_m ** 2), 2)
    
    @property
    def has_data(self):
        """Check if any health metrics data exists."""
        fields = [
            self.height_cm, self.weight_kg, self.bmi,
            self.systolic_bp, self.diastolic_bp, self.heart_rate,
            self.fasting_glucose, self.hba1c,
            self.total_cholesterol, self.ldl, self.hdl, self.triglycerides,
            self.sgot, self.sgpt,
            self.creatinine, self.uric_acid
        ]
        return any(f is not None for f in fields)
    
    def to_dict(self):
        """Convert metrics to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'mcu_record_id': self.mcu_record_id,
            # Basic Measurements
            'height_cm': self.height_cm,
            'weight_kg': self.weight_kg,
            'bmi': self.bmi,
            # Vital Signs
            'systolic_bp': self.systolic_bp,
            'diastolic_bp': self.diastolic_bp,
            'heart_rate': self.heart_rate,
            # Blood Sugar
            'fasting_glucose': self.fasting_glucose,
            'hba1c': self.hba1c,
            # Lipid Profile
            'total_cholesterol': self.total_cholesterol,
            'ldl': self.ldl,
            'hdl': self.hdl,
            'triglycerides': self.triglycerides,
            # Liver Function
            'sgot': self.sgot,
            'sgpt': self.sgpt,
            # Kidney Function
            'creatinine': self.creatinine,
            'uric_acid': self.uric_acid,
            # Notes
            'doctor_notes': self.doctor_notes
        }