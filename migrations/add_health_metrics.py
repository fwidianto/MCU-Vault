"""
Migration: Add HealthMetrics Table

This migration adds the health_metrics table for storing structured medical check-up data.
Safe for existing production data - preserves all existing records.

Run with: python -c "from migrations.add_health_metrics import upgrade; upgrade()"
"""
from app import db


def upgrade():
    """
    Add health_metrics table to database.
    All fields allow NULL values for flexibility.
    """
    # Create the health_metrics table
    db.create_all()
    print("HealthMetrics table created successfully.")


def downgrade():
    """
    Remove health_metrics table from database.
    WARNING: This will delete all health metrics data.
    """
    from sqlalchemy import text
    try:
        db.session.execute(text("DROP TABLE IF EXISTS health_metrics CASCADE"))
        db.session.commit()
        print("HealthMetrics table dropped.")
    except Exception as e:
        print(f"Error dropping table: {e}")
        db.session.rollback()


if __name__ == '__main__':
    # Allow running migration directly
    from run import app
    with app.app_context():
        if len(__import__('sys').argv) > 1 and __import__('sys').argv[1] == 'downgrade':
            downgrade()
        else:
            upgrade()