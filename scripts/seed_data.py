#!/usr/bin/env python3
"""
MCU Vault Data Seeding Utility

Generates realistic historical MCU data for testing Phase 2B analytics.
Creates demo user, MCU records, and health metrics with believable trends.

Usage:
    python scripts/seed_data.py              # Seed demo data
    python scripts/seed_data.py --reset       # Reset and reseed
    python scripts/seed_data.py --user-email user@example.com  # Seed for specific user
"""

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from app.models import User, MCURecord, HealthMetrics
from werkzeug.security import generate_password_hash


class HealthDataGenerator:
    """Generates realistic health data with believable trends over time."""
    
    def __init__(self, base_year=2012, end_year=2026):
        self.base_year = base_year
        self.end_year = end_year
        self.years = list(range(base_year, end_year + 1))
        
        # Base profile: healthy 30-year-old male
        self.base_profile = {
            'height_cm': 175,
            'weight_kg': 75,  # Starting healthy
            'systolic_bp': 118,
            'diastolic_bp': 76,
            'heart_rate': 72,
            'fasting_glucose': 92,
            'hba1c': 5.4,
            'total_cholesterol': 185,
            'ldl': 105,
            'hdl': 55,
            'triglycerides': 120,
            'sgot': 28,
            'sgpt': 30,
            'creatinine': 0.95,
            'uric_acid': 5.8,
        }
    
    def get_trend_factor(self, year):
        """
        Calculate trend multipliers based on year.
        Returns factors that create believable health progression.
        """
        years_from_start = year - self.base_year
        
        # Phase 1 (2012-2017): Healthy baseline with slight decline
        # Phase 2 (2018-2021): Weight gain, cholesterol rising
        # Phase 3 (2022-2023): Prediabetes, hypertension
        # Phase 4 (2024-2025): Lifestyle changes, improvement
        # Phase 5 (2026): Continued improvement
        
        if year <= 2017:
            # Healthy years, slight aging
            age_factor = 1 + (years_from_start * 0.005)
            weight_trend = 1 + (years_from_start * 0.008)
        elif year <= 2021:
            # Weight gain, cholesterol rising
            years_into_phase = year - 2018
            age_factor = 1.03
            weight_trend = 1.05 + (years_into_phase * 0.02)
            cholesterol_trend = 1 + (years_into_phase * 0.03)
            glucose_trend = 1 + (years_into_phase * 0.015)
        elif year <= 2023:
            # Prediabetes and borderline hypertension
            years_into_phase = year - 2022
            age_factor = 1.05
            weight_trend = 1.12 + (years_into_phase * 0.01)
            bp_trend = 1 + (years_into_phase * 0.04)
            glucose_trend = 1.08 + (years_into_phase * 0.02)
            hba1c_trend = 1 + (years_into_phase * 0.03)
        else:
            # Lifestyle improvements
            years_into_phase = year - 2024
            age_factor = 1.06
            weight_trend = 1.14 - (years_into_phase * 0.03)
            bp_trend = 1.08 - (years_into_phase * 0.02)
            glucose_trend = 1.14 - (years_into_phase * 0.025)
            hba1c_trend = 1.09 - (years_into_phase * 0.02)
            cholesterol_trend = 1.12 - (years_into_phase * 0.02)
        
        return {
            'age': age_factor,
            'weight': weight_trend if 'weight_trend' in locals() else 1 + (years_from_start * 0.008),
            'systolic_bp': bp_trend if 'bp_trend' in locals() else 1 + (years_from_start * 0.005),
            'diastolic_bp': bp_trend if 'bp_trend' in locals() else 1 + (years_from_start * 0.005),
            'heart_rate': 1 - (years_from_start * 0.002),  # Slight decrease with age
            'fasting_glucose': glucose_trend if 'glucose_trend' in locals() else 1 + (years_from_start * 0.008),
            'hba1c': hba1c_trend if 'hba1c_trend' in locals() else 1 + (years_from_start * 0.008),
            'total_cholesterol': cholesterol_trend if 'cholesterol_trend' in locals() else 1 + (years_from_start * 0.01),
            'ldl': cholesterol_trend * 1.02 if 'cholesterol_trend' in locals() else 1 + (years_from_start * 0.012),
            'hdl': 1 - (years_from_start * 0.003),  # HDL decreases slightly
            'triglycerides': 1 + (years_from_start * 0.015),
            'sgot': 1 + (years_from_start * 0.008),
            'sgpt': 1 + (years_from_start * 0.01),
            'creatinine': 1 + (years_from_start * 0.005),
            'uric_acid': 1 + (years_from_start * 0.012),
        }
    
    def add_variation(self, value, variation_percent=0.05):
        """Add realistic random variation to values."""
        variation = random.uniform(-variation_percent, variation_percent)
        return round(value * (1 + variation), 1)
    
    def generate_health_data(self, year):
        """Generate health data for a specific year with realistic trends."""
        trend = self.get_trend_factor(year)
        data = {}
        
        for metric, base_value in self.base_profile.items():
            # Apply trend
            new_value = base_value * trend.get(metric, 1)
            
            # Add seasonal/lifestyle variation
            new_value = self.add_variation(new_value, 0.03)
            
            # Round appropriately for each metric type
            if metric in ['bmi', 'hba1c', 'uric_acid']:
                data[metric] = round(new_value, 1)
            elif metric in ['height_cm']:
                data[metric] = round(new_value)  # Height doesn't change much
            else:
                data[metric] = round(new_value, 1)
        
        # Auto-calculate BMI from height and weight
        height_m = data['height_cm'] / 100
        data['bmi'] = round(data['weight_kg'] / (height_m * height_m), 1)
        
        # Add specific markers for different years
        if year == 2015:
            data['weight_kg'] = self.add_variation(77, 0.02)  # Starting to gain
        elif year == 2018:
            data['ldl'] = self.add_variation(125, 0.03)  # LDL rising
        elif year == 2021:
            data['fasting_glucose'] = self.add_variation(112, 0.02)  # Prediabetes threshold
            data['hba1c'] = self.add_variation(6.0, 0.02)
        elif year == 2023:
            data['systolic_bp'] = self.add_variation(138, 0.02)  # Borderline hypertension
            data['diastolic_bp'] = self.add_variation(88, 0.02)
        elif year == 2025:
            # Lifestyle improvements
            data['weight_kg'] = self.add_variation(78, 0.02)
            data['fasting_glucose'] = self.add_variation(100, 0.02)
            data['hba1c'] = self.add_variation(5.7, 0.02)
        elif year == 2026:
            # Continued improvement
            data['weight_kg'] = self.add_variation(76, 0.02)
            data['bmi'] = round(data['weight_kg'] / ((data['height_cm'] / 100) ** 2), 1)
            data['systolic_bp'] = self.add_variation(128, 0.02)
            data['diastolic_bp'] = self.add_variation(82, 0.02)
            data['fasting_glucose'] = self.add_variation(95, 0.02)
            data['hba1c'] = self.add_variation(5.5, 0.02)
        
        return data


def create_demo_user(email='demo@mcu-vault.com', password='demo123'):
    """Create demo user account."""
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    
    user = User(
        username='demo',
        email=email
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def seed_data_for_user(user_id, reset=False):
    """Seed MCU records and health metrics for a specific user."""
    generator = HealthDataGenerator()
    
    records_created = 0
    metrics_created = 0
    
    if reset:
        # Delete existing records for this user
        HealthMetrics.query.filter(
            HealthMetrics.mcu_record_id.in_(
                db.session.query(MCURecord.id).filter(MCURecord.user_id == user_id)
            )
        ).delete(synchronize_session=False)
        
        MCURecord.query.filter_by(user_id=user_id).delete()
        db.session.commit()
    
    # Generate 15 records spanning 2012-2026
    # Spacing: more frequent in recent years
    year_spacing = {
        2012: 0, 2013: 0, 2014: 0, 2015: 0,  # Every year early on
        2016: 0, 2017: 0, 
        2018: 6,  # Every 6 months
        2019: 6, 2020: 6, 2021: 6,
        2022: 3,  # Every 3 months
        2023: 3, 2024: 3, 2025: 3, 2026: 0
    }
    
    mcu_dates = []
    for year in generator.years:
        base_date = datetime(year, 4, 15)  # April checkup
        if year <= 2017:
            mcu_dates.append(base_date)
        elif year <= 2021:
            # Two checkups per year
            mcu_dates.append(base_date)
            mcu_dates.append(datetime(year, 10, 15))
        else:
            # Four checkups per year
            for month in [3, 6, 9, 12]:
                mcu_dates.append(datetime(year, month, 15))
    
    # Take only 15 records
    mcu_dates = sorted(mcu_dates)[:15]
    
    for i, mcu_date in enumerate(mcu_dates):
        year = mcu_date.year
        health_data = generator.generate_health_data(year)
        
        # Create MCU record
        record = MCURecord(
            user_id=user_id,
            patient_name='Demo Patient',
            company=random.choice(['Tech Corp', 'Health Inc', 'Finance Ltd', None]),
            mcu_date=mcu_date,
            status=random.choice(['completed', 'completed', 'completed', 'pending']),
            notes=f'Annual MCU for {year}'
        )
        db.session.add(record)
        db.session.flush()
        records_created += 1
        
        # Create health metrics
        metrics = HealthMetrics(
            mcu_record_id=record.id,
            height_cm=health_data['height_cm'],
            weight_kg=health_data['weight_kg'],
            bmi=health_data['bmi'],
            systolic_bp=health_data['systolic_bp'],
            diastolic_bp=health_data['diastolic_bp'],
            heart_rate=health_data['heart_rate'],
            fasting_glucose=health_data['fasting_glucose'],
            hba1c=health_data['hba1c'],
            total_cholesterol=health_data['total_cholesterol'],
            ldl=health_data['ldl'],
            hdl=health_data['hdl'],
            triglycerides=health_data['triglycerides'],
            sgot=health_data['sgot'],
            sgpt=health_data['sgpt'],
            creatinine=health_data['creatinine'],
            uric_acid=health_data['uric_acid'],
            doctor_notes=_get_doctor_notes(year, health_data)
        )
        db.session.add(metrics)
        metrics_created += 1
    
    db.session.commit()
    
    return {
        'records_created': records_created,
        'metrics_created': metrics_created
    }


def _get_doctor_notes(year, health_data):
    """Generate contextual doctor notes based on health trends."""
    notes = []
    
    bmi = health_data['bmi']
    if bmi >= 30:
        notes.append('Recommend weight management program.')
    elif bmi >= 25:
        notes.append('Consider lifestyle modifications.')
    
    bp = health_data['systolic_bp']
    if bp >= 140:
        notes.append('Elevated blood pressure - monitor closely.')
    elif bp >= 130:
        notes.append('Borderline elevated blood pressure.')
    
    glucose = health_data['fasting_glucose']
    if glucose >= 126:
        notes.append('Fasting glucose indicates diabetes - follow up required.')
    elif glucose >= 100:
        notes.append('Fasting glucose slightly elevated - dietary recommendations.')
    
    hba1c = health_data['hba1c']
    if hba1c >= 6.5:
        notes.append('HbA1c indicates diabetes management needed.')
    elif hba1c >= 5.7:
        notes.append('HbA1c in prediabetes range.')
    
    ldl = health_data['ldl']
    if ldl >= 160:
        notes.append('LDL cholesterol elevated - consider statin therapy.')
    elif ldl >= 130:
        notes.append('LDL cholesterol borderline high.')
    
    if year >= 2024:
        notes.append('Lifestyle improvements showing positive results.')
    
    return ' '.join(notes) if notes else 'Overall health status satisfactory.'


def main():
    parser = argparse.ArgumentParser(
        description='Seed MCU Vault with realistic test data.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                        Seed demo data
  %(prog)s --reset                Reset and reseed demo data
  %(prog)s --user-email user@test.com  Seed data for specific user
        """
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Delete existing demo data before reseeding'
    )
    parser.add_argument(
        '--user-email',
        type=str,
        default='demo@mcu-vault.com',
        help='Email for the user to seed data for (default: demo@mcu-vault.com)'
    )
    
    args = parser.parse_args()
    
    # Create Flask app context
    app = create_app('production')
    
    with app.app_context():
        # Initialize database
        db.create_all()
        
        print("\n" + "=" * 50)
        print("MCU Vault Data Seeding Utility")
        print("=" * 50 + "\n")
        
        # Create or get user
        print(f"User Email: {args.user_email}")
        user = create_demo_user(email=args.user_email)
        print(f"User ID: {user.id}")
        
        # Seed data
        print("\nSeeding data...")
        result = seed_data_for_user(user.id, reset=args.reset)
        
        # Print summary
        print("\n" + "-" * 50)
        print("SUMMARY")
        print("-" * 50)
        print(f"Users Created:        1")
        print(f"MCU Records Created:   {result['records_created']}")
        print(f"Health Metrics Created: {result['metrics_created']}")
        print("-" * 50)
        print("\nSeeding complete!")
        print("\nDemo credentials:")
        print("  Email:    demo@mcu-vault.com")
        print("  Password: demo123")
        print("\n" + "=" * 50)


if __name__ == '__main__':
    main()