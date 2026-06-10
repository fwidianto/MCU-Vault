"""
Tests for the MCU Vault seed data utility.

Validates that the seed script generates realistic, believable health data
with proper trends over time.
"""

import pytest
from datetime import datetime
from app import create_app, db
from app.models import User, MCURecord, HealthMetrics
from scripts.seed_data import (
    HealthDataGenerator,
    create_demo_user,
    seed_data_for_user,
    _get_doctor_notes
)


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestHealthDataGenerator:
    """Tests for the HealthDataGenerator class."""
    
    def test_generator_initialization(self):
        """Test that generator initializes with correct years."""
        generator = HealthDataGenerator(base_year=2012, end_year=2026)
        
        assert generator.base_year == 2012
        assert generator.end_year == 2026
        assert 2012 in generator.years
        assert 2026 in generator.years
    
    def test_base_profile_exists(self):
        """Test that base profile contains all required metrics."""
        generator = HealthDataGenerator()
        
        # BMI is calculated from height/weight, not stored in base_profile
        required_metrics = [
            'height_cm', 'weight_kg',
            'systolic_bp', 'diastolic_bp', 'heart_rate',
            'fasting_glucose', 'hba1c',
            'total_cholesterol', 'ldl', 'hdl', 'triglycerides',
            'sgot', 'sgpt', 'creatinine', 'uric_acid'
        ]
        
        for metric in required_metrics:
            assert metric in generator.base_profile
    
    def test_generate_health_data_returns_all_metrics(self):
        """Test that generated data contains all required metrics."""
        generator = HealthDataGenerator()
        
        for year in [2012, 2018, 2021, 2023, 2026]:
            data = generator.generate_health_data(year)
            
            required_metrics = [
                'height_cm', 'weight_kg', 'bmi',
                'systolic_bp', 'diastolic_bp', 'heart_rate',
                'fasting_glucose', 'hba1c',
                'total_cholesterol', 'ldl', 'hdl', 'triglycerides',
                'sgot', 'sgpt', 'creatinine', 'uric_acid'
            ]
            
            for metric in required_metrics:
                assert metric in data, f"Missing metric: {metric} for year {year}"
    
    def test_bmi_calculated_from_height_and_weight(self):
        """Test that BMI is correctly calculated from height and weight."""
        generator = HealthDataGenerator()
        
        data = generator.generate_health_data(2020)
        
        expected_bmi = data['weight_kg'] / ((data['height_cm'] / 100) ** 2)
        assert abs(data['bmi'] - round(expected_bmi, 1)) < 0.5
    
    def test_health_trends_over_time(self):
        """Test that health metrics show believable progression over years."""
        generator = HealthDataGenerator()
        
        # Weight should generally increase from 2012 to 2021
        weight_2012 = generator.generate_health_data(2012)['weight_kg']
        weight_2021 = generator.generate_health_data(2021)['weight_kg']
        
        assert weight_2021 > weight_2012 * 0.95, \
            "Weight trend should be relatively stable or increasing"
        
        # Glucose should show increase in later years
        glucose_2012 = generator.generate_health_data(2012)['fasting_glucose']
        glucose_2021 = generator.generate_health_data(2021)['fasting_glucose']
        
        assert glucose_2021 > glucose_2012 * 0.90, \
            "Glucose trend should show increase"
    
    def test_variation_is_within_bounds(self):
        """Test that generated values have reasonable variation."""
        generator = HealthDataGenerator()
        
        # Generate multiple times for same year and check variation
        weights = [generator.generate_health_data(2020)['weight_kg'] for _ in range(10)]
        
        min_weight = min(weights)
        max_weight = max(weights)
        variation = (max_weight - min_weight) / min_weight
        
        assert variation < 0.15, \
            f"Weight variation {variation:.2%} is too high (should be < 15%)"


class TestCreateDemoUser:
    """Tests for the create_demo_user function."""
    
    def test_create_new_user(self, app):
        """Test creating a new demo user."""
        with app.app_context():
            email = 'test@example.com'
            user = create_demo_user(email=email, password='testpass123')
            
            assert user is not None
            assert user.email == email
            assert user.username == 'demo'
            assert user.check_password('testpass123')
    
    def test_return_existing_user(self, app):
        """Test that existing user is returned without creating new."""
        with app.app_context():
            email = 'existing@example.com'
            
            # Create user first time
            user1 = create_demo_user(email=email, password='pass1')
            user1_id = user1.id
            
            # Create again - should return existing user with original password
            user2 = create_demo_user(email=email, password='pass2')
            
            assert user2.id == user1_id
            assert user2.check_password('pass1')  # Original password preserved


class TestSeedDataForUser:
    """Tests for the seed_data_for_user function."""
    
    def test_seed_creates_records(self, app):
        """Test that seeding creates the expected number of records."""
        with app.app_context():
            # Create user first
            user = create_demo_user(email='seedtest@example.com')
            
            # Seed data
            result = seed_data_for_user(user.id)
            
            assert result['records_created'] == 15
            assert result['metrics_created'] == 15
            
            # Verify in database
            assert MCURecord.query.filter_by(user_id=user.id).count() == 15
            assert HealthMetrics.query.join(MCURecord).filter(
                MCURecord.user_id == user.id
            ).count() == 15
    
    def test_seed_reset_clears_data(self, app):
        """Test that --reset clears existing data."""
        with app.app_context():
            user = create_demo_user(email='reset@example.com')
            
            # Seed initial data
            seed_data_for_user(user.id)
            assert MCURecord.query.filter_by(user_id=user.id).count() == 15
            
            # Seed with reset
            result = seed_data_for_user(user.id, reset=True)
            
            # Should still have 15 records (reset then recreated)
            assert MCURecord.query.filter_by(user_id=user.id).count() == 15
    
    def test_records_have_realistic_dates(self, app):
        """Test that records span the expected date range."""
        with app.app_context():
            user = create_demo_user(email='dates@example.com')
            seed_data_for_user(user.id)
            
            records = MCURecord.query.filter_by(user_id=user.id).order_by(MCURecord.mcu_date).all()
            
            assert len(records) == 15
            assert records[0].mcu_date.year >= 2012
            assert records[-1].mcu_date.year <= 2026
    
    def test_health_metrics_have_doctor_notes(self, app):
        """Test that health metrics include doctor notes."""
        with app.app_context():
            user = create_demo_user(email='notes@example.com')
            seed_data_for_user(user.id)
            
            records = MCURecord.query.filter_by(user_id=user.id).all()
            
            for record in records:
                metrics = HealthMetrics.query.filter_by(mcu_record_id=record.id).first()
                assert metrics is not None
                assert metrics.doctor_notes is not None
                assert len(metrics.doctor_notes) > 0


class TestDoctorNotes:
    """Tests for the _get_doctor_notes function."""
    
    def test_returns_string(self):
        """Test that doctor notes returns a string."""
        health_data = {
            'bmi': 25,
            'systolic_bp': 130,
            'fasting_glucose': 100,
            'hba1c': 5.8,
            'ldl': 140
        }
        
        notes = _get_doctor_notes(2020, health_data)
        assert isinstance(notes, str)
        assert len(notes) > 0
    
    def test_notes_reflect_health_status(self):
        """Test that doctor notes reflect the health data."""
        # High BMI
        health_data = {'bmi': 32, 'systolic_bp': 120, 'fasting_glucose': 95, 'hba1c': 5.5, 'ldl': 110}
        notes = _get_doctor_notes(2020, health_data)
        assert 'weight' in notes.lower() or 'lifestyle' in notes.lower()
        
        # High blood pressure
        health_data = {'bmi': 24, 'systolic_bp': 145, 'fasting_glucose': 95, 'hba1c': 5.5, 'ldl': 110}
        notes = _get_doctor_notes(2020, health_data)
        assert 'blood pressure' in notes.lower() or 'elevated' in notes.lower()


class TestIntegration:
    """Integration tests for the complete seed workflow."""
    
    def test_full_seed_workflow(self, app):
        """Test the complete seed workflow from start to finish."""
        with app.app_context():
            # Create user
            user = create_demo_user(email='integration@example.com')
            
            # Seed data
            result = seed_data_for_user(user.id)
            
            # Verify summary counts
            assert result['records_created'] == 15
            assert result['metrics_created'] == 15
            
            # Verify user has records
            assert user.mcu_records.count() == 15
            
            # Verify all records have health metrics
            for record in user.mcu_records.all():
                metrics = HealthMetrics.query.filter_by(mcu_record_id=record.id).first()
                assert metrics is not None
    
    def test_seed_data_supports_analytics(self, app):
        """Test that seeded data provides sufficient data for analytics."""
        with app.app_context():
            user = create_demo_user(email='analytics@example.com')
            seed_data_for_user(user.id)
            
            records = MCURecord.query.filter_by(user_id=user.id).all()
            
            # Should have at least 10 records for meaningful analytics
            assert len(records) >= 10
            
            # Should span multiple years
            years = [r.mcu_date.year for r in records]
            assert len(set(years)) >= 5  # At least 5 different years
            
            # Should have varying health metrics for trend analysis
            metrics_list = []
            for record in records:
                m = HealthMetrics.query.filter_by(mcu_record_id=record.id).first()
                if m:
                    metrics_list.append({
                        'bmi': m.bmi,
                        'systolic_bp': m.systolic_bp,
                        'fasting_glucose': m.fasting_glucose
                    })
            
            # BMI should vary across records
            bmis = [m['bmi'] for m in metrics_list]
            assert max(bmis) - min(bmis) > 1, "BMI should show variation for analytics"