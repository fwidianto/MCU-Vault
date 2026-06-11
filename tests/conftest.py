"""
Test configuration and fixtures for MCU Vault Phase 2B.
"""
import pytest
from datetime import date, datetime
from app import create_app, db
from app.models.user import User
from app.models.mcu_record import MCURecord
from app.models.health_metrics import HealthMetrics


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Create authenticated test client."""
    with app.app_context():
        # Create test user
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
    
    # Login using POST to the login route (Flask-Login uses this)
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True
    
    # Store the app context for later use
    client._app_context = app.app_context()
    
    return client


@pytest.fixture
def sample_user(app):
    """Create a sample user."""
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User(
                username='testuser',
                email='test@example.com'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def sample_records_with_metrics(app, sample_user):
    """Create sample MCU records with health metrics for testing."""
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        
        records = []
        
        # Record 1 - January 2024
        record1 = MCURecord(
            patient_name='John Doe',
            company='Acme Corp',
            mcu_date=date(2024, 1, 15),
            status='cleared',
            user_id=user.id
        )
        db.session.add(record1)
        db.session.flush()
        
        metrics1 = HealthMetrics(
            mcu_record_id=record1.id,
            height_cm=175,
            weight_kg=75,
            bmi=24.49,
            systolic_bp=120,
            diastolic_bp=80,
            heart_rate=72,
            fasting_glucose=95,
            hba1c=5.4,
            total_cholesterol=190,
            ldl=110,
            hdl=55,
            triglycerides=130,
            sgot=25,
            sgpt=28,
            creatinine=1.0,
            uric_acid=5.5
        )
        db.session.add(metrics1)
        records.append(record1)
        
        # Record 2 - June 2024
        record2 = MCURecord(
            patient_name='John Doe',
            company='Acme Corp',
            mcu_date=date(2024, 6, 20),
            status='cleared',
            user_id=user.id
        )
        db.session.add(record2)
        db.session.flush()
        
        metrics2 = HealthMetrics(
            mcu_record_id=record2.id,
            height_cm=175,
            weight_kg=78,
            bmi=25.47,
            systolic_bp=128,
            diastolic_bp=82,
            heart_rate=75,
            fasting_glucose=105,
            hba1c=5.8,
            total_cholesterol=210,
            ldl=135,
            hdl=52,
            triglycerides=150,
            sgot=28,
            sgpt=32,
            creatinine=1.1,
            uric_acid=6.0
        )
        db.session.add(metrics2)
        records.append(record2)
        
        # Record 3 - December 2024
        record3 = MCURecord(
            patient_name='John Doe',
            company='Acme Corp',
            mcu_date=date(2024, 12, 10),
            status='needs-follow-up',
            user_id=user.id
        )
        db.session.add(record3)
        db.session.flush()
        
        metrics3 = HealthMetrics(
            mcu_record_id=record3.id,
            height_cm=175,
            weight_kg=82,
            bmi=26.78,
            systolic_bp=135,
            diastolic_bp=88,
            heart_rate=78,
            fasting_glucose=115,
            hba1c=6.2,
            total_cholesterol=225,
            ldl=150,
            hdl=48,
            triglycerides=180,
            sgot=30,
            sgpt=35,
            creatinine=1.2,
            uric_acid=6.5
        )
        db.session.add(metrics3)
        records.append(record3)
        
        db.session.commit()
        
        return {
            'record1': record1.id,
            'record2': record2.id,
            'record3': record3.id,
            'user_id': user.id
        }


@pytest.fixture
def single_record_with_metrics(app, sample_user):
    """Create a single MCU record with health metrics for testing."""
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        
        record = MCURecord(
            patient_name='Jane Smith',
            company='Tech Inc',
            mcu_date=date(2024, 3, 10),
            status='cleared',
            user_id=user.id
        )
        db.session.add(record)
        db.session.flush()
        
        metrics = HealthMetrics(
            mcu_record_id=record.id,
            height_cm=165,
            weight_kg=60,
            bmi=22.04,
            systolic_bp=115,
            diastolic_bp=75,
            heart_rate=68,
            fasting_glucose=90,
            hba1c=5.2,
            total_cholesterol=175,
            ldl=95,
            hdl=65,
            triglycerides=100
        )
        db.session.add(metrics)
        db.session.commit()
        
        return {
            'record_id': record.id,
            'user_id': user.id
        }