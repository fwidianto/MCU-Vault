"""
Health Analytics routes for Phase 2B.
Trend analysis, historical comparisons, and health status classification.
"""
from flask import Blueprint, render_template, request, jsonify, make_response, Response
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime
import csv
import io

from app import db
from app.models.mcu_record import MCURecord
from app.models.health_metrics import HealthMetrics
from app.utils.health_classification import (
    HealthClassifier, classify_all_metrics, 
    calculate_difference, get_trend_indicator,
    format_metric_value, HealthLevel
)

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/dashboard/health')
@login_required
def health_dashboard():
    """Display the health analytics dashboard with latest snapshot and status."""
    # Get the most recent MCU record with health metrics
    latest_record = MCURecord.query.filter_by(
        user_id=current_user.id
    ).join(HealthMetrics).order_by(
        MCURecord.mcu_date.desc()
    ).first()
    
    # Get total records with metrics
    total_with_metrics = db.session.query(func.count(HealthMetrics.id)).join(
        MCURecord
    ).filter(MCURecord.user_id == current_user.id).scalar() or 0
    
    # Get all records for trend data (need at least 2 for trends)
    records_for_trends = MCURecord.query.filter_by(
        user_id=current_user.id
    ).join(HealthMetrics).order_by(
        MCURecord.mcu_date.asc()
    ).all()
    
    has_sufficient_data = len(records_for_trends) >= 1
    
    # Get latest health metrics and classify them
    latest_metrics = None
    classifications = {}
    
    if latest_record and latest_record.health_metrics:
        latest_metrics = latest_record.health_metrics
        classifications = classify_all_metrics(latest_metrics)
    
    # Get latest MCU date
    latest_mcu_date = None
    if latest_record:
        latest_mcu_date = latest_record.mcu_date
    
    context = {
        'latest_record': latest_record,
        'latest_metrics': latest_metrics,
        'classifications': classifications,
        'latest_mcu_date': latest_mcu_date,
        'total_with_metrics': total_with_metrics,
        'has_sufficient_data': has_sufficient_data,
        'records_count': len(records_for_trends)
    }
    
    return render_template('analytics/health_dashboard.html', **context)


@analytics_bp.route('/api/trends')
@login_required
def get_trend_data():
    """
    API endpoint to get trend data for charts.
    Returns data in a format suitable for Chart.js.
    """
    # Get all records with health metrics, ordered by date
    records = MCURecord.query.filter_by(
        user_id=current_user.id
    ).join(HealthMetrics).order_by(
        MCURecord.mcu_date.asc()
    ).all()
    
    if not records or len(records) < 1:
        return jsonify({
            'error': 'Not enough data',
            'message': 'At least one record with health metrics is needed for trends.',
            'records_count': len(records)
        })
    
    # Build trend data
    labels = []
    body_measurements = {
        'weight': [],
        'bmi': [],
        'height': []
    }
    blood_pressure = {
        'systolic': [],
        'diastolic': []
    }
    blood_sugar = {
        'fasting_glucose': [],
        'hba1c': []
    }
    lipid_profile = {
        'total_cholesterol': [],
        'ldl': [],
        'hdl': [],
        'triglycerides': []
    }
    
    for record in records:
        # Add date label
        labels.append(record.mcu_date.strftime('%Y-%m-%d') if record.mcu_date else '')
        
        metrics = record.health_metrics
        if metrics:
            # Body measurements
            body_measurements['weight'].append(metrics.weight_kg)
            body_measurements['bmi'].append(metrics.bmi)
            body_measurements['height'].append(metrics.height_cm)
            
            # Blood pressure
            blood_pressure['systolic'].append(metrics.systolic_bp)
            blood_pressure['diastolic'].append(metrics.diastolic_bp)
            
            # Blood sugar
            blood_sugar['fasting_glucose'].append(metrics.fasting_glucose)
            blood_sugar['hba1c'].append(metrics.hba1c)
            
            # Lipid profile
            lipid_profile['total_cholesterol'].append(metrics.total_cholesterol)
            lipid_profile['ldl'].append(metrics.ldl)
            lipid_profile['hdl'].append(metrics.hdl)
            lipid_profile['triglycerides'].append(metrics.triglycerides)
    
    return jsonify({
        'labels': labels,
        'body_measurements': body_measurements,
        'blood_pressure': blood_pressure,
        'blood_sugar': blood_sugar,
        'lipid_profile': lipid_profile,
        'records_count': len(records)
    })


@analytics_bp.route('/records/compare')
@login_required
def compare():
    """Display MCU record comparison page."""
    # Get all records with health metrics for selection
    records = MCURecord.query.filter_by(
        user_id=current_user.id
    ).join(HealthMetrics).order_by(
        MCURecord.mcu_date.desc()
    ).all()
    
    # Get selected records
    record_a_id = request.args.get('record_a', type=int)
    record_b_id = request.args.get('record_b', type=int)
    
    record_a = None
    record_b = None
    comparison_data = None
    
    if record_a_id and record_b_id:
        record_a = MCURecord.query.filter_by(
            id=record_a_id, user_id=current_user.id
        ).first()
        record_b = MCURecord.query.filter_by(
            id=record_b_id, user_id=current_user.id
        ).first()
        
        if record_a and record_b and record_a.health_metrics and record_b.health_metrics:
            comparison_data = calculate_comparison(record_a, record_b)
    
    context = {
        'records': records,
        'record_a': record_a,
        'record_b': record_b,
        'comparison_data': comparison_data
    }
    
    return render_template('records/compare.html', **context)


def calculate_comparison(record_a: MCURecord, record_b: MCURecord) -> dict:
    """
    Calculate comparison between two MCU records.
    
    Args:
        record_a: Earlier or first MCU record
        record_b: Later or second MCU record
        
    Returns:
        Dictionary with comparison data
    """
    metrics_a = record_a.health_metrics
    metrics_b = record_b.health_metrics
    
    if not metrics_a or not metrics_b:
        return None
    
    # Define metrics to compare
    comparison_metrics = [
        ('weight_kg', 'Weight', 'kg', True),
        ('bmi', 'BMI', '', True),
        ('height_cm', 'Height', 'cm', False),
        ('systolic_bp', 'Systolic BP', 'mmHg', True),
        ('diastolic_bp', 'Diastolic BP', 'mmHg', True),
        ('heart_rate', 'Heart Rate', 'bpm', True),
        ('fasting_glucose', 'Fasting Glucose', 'mg/dL', True),
        ('hba1c', 'HbA1c', '%', True),
        ('total_cholesterol', 'Total Cholesterol', 'mg/dL', True),
        ('ldl', 'LDL', 'mg/dL', True),
        ('hdl', 'HDL', 'mg/dL', False),  # Higher is better
        ('triglycerides', 'Triglycerides', 'mg/dL', True),
        ('sgot', 'SGOT/AST', 'U/L', True),
        ('sgpt', 'SGPT/ALT', 'U/L', True),
        ('creatinine', 'Creatinine', 'mg/dL', True),
        ('uric_acid', 'Uric Acid', 'mg/dL', True),
    ]
    
    results = []
    
    for field, label, unit, lower_is_better in comparison_metrics:
        value_a = getattr(metrics_a, field)
        value_b = getattr(metrics_b, field)
        
        if value_a is not None or value_b is not None:
            diff, _ = calculate_difference(value_a, value_b)
            trend = get_trend_indicator(diff, lower_is_better)
            
            # Determine overall trend based on metric type
            # For most health metrics, lower is generally better
            # But for HDL, higher is better
            if field == 'hdl':
                trend = 'improvement' if diff > 0 else ('worsening' if diff < 0 else 'no_change')
            
            results.append({
                'field': field,
                'label': label,
                'unit': unit,
                'value_a': value_a,
                'value_b': value_b,
                'formatted_a': format_metric_value(value_a, unit),
                'formatted_b': format_metric_value(value_b, unit),
                'difference': diff,
                'formatted_diff': _format_difference(diff, unit),
                'trend': trend,
                'has_both_values': value_a is not None and value_b is not None
            })
    
    # Add date information
    date_a = record_a.mcu_date.strftime('%B %d, %Y') if record_a.mcu_date else 'N/A'
    date_b = record_b.mcu_date.strftime('%B %d, %Y') if record_b.mcu_date else 'N/A'
    
    # Calculate days between
    days_between = None
    if record_a.mcu_date and record_b.mcu_date:
        days_between = abs((record_b.mcu_date - record_a.mcu_date).days)
    
    return {
        'metrics': results,
        'record_a_info': {
            'id': record_a.id,
            'patient_name': record_a.patient_name,
            'date': date_a,
            'mcu_date': record_a.mcu_date
        },
        'record_b_info': {
            'id': record_b.id,
            'patient_name': record_b.patient_name,
            'date': date_b,
            'mcu_date': record_b.mcu_date
        },
        'days_between': days_between
    }


def _format_difference(diff: float, unit: str) -> str:
    """Format difference for display."""
    if diff is None:
        return 'N/A'
    
    sign = '+' if diff > 0 else ''
    if unit:
        return f"{sign}{diff:.1f} {unit}"
    return f"{sign}{diff:.2f}"


@analytics_bp.route('/records/compare/export')
@login_required
def export_comparison():
    """Export comparison results as CSV."""
    record_a_id = request.args.get('record_a', type=int)
    record_b_id = request.args.get('record_b', type=int)
    
    if not record_a_id or not record_b_id:
        return jsonify({'error': 'Both records must be selected'}), 400
    
    record_a = MCURecord.query.filter_by(
        id=record_a_id, user_id=current_user.id
    ).first()
    record_b = MCURecord.query.filter_by(
        id=record_b_id, user_id=current_user.id
    ).first()
    
    if not record_a or not record_b:
        return jsonify({'error': 'Records not found'}), 404
    
    comparison = calculate_comparison(record_a, record_b)
    
    if not comparison:
        return jsonify({'error': 'Cannot compare - missing health metrics'}), 400
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'MCU Vault - Health Comparison Report',
        '',
        '',
        ''
    ])
    writer.writerow([
        f"Record A: {comparison['record_a_info']['patient_name']}",
        f"Date: {comparison['record_a_info']['date']}",
        '',
        ''
    ])
    writer.writerow([
        f"Record B: {comparison['record_b_info']['patient_name']}",
        f"Date: {comparison['record_b_info']['date']}",
        '',
        ''
    ])
    if comparison['days_between']:
        writer.writerow([
            f"Days Between: {comparison['days_between']}",
            '',
            '',
            ''
        ])
    writer.writerow([])
    
    # Metric comparison header
    writer.writerow(['Metric', f"Record A ({comparison['record_a_info']['date']})", 
                     f"Record B ({comparison['record_b_info']['date']})", 'Difference', 'Trend'])
    
    # Data rows
    for metric in comparison['metrics']:
        trend_display = {
            'improvement': '↓ Improvement',
            'worsening': '↑ Worsening',
            'no_change': '— No Change',
            'unknown': '? Unknown'
        }.get(metric['trend'], metric['trend'])
        
        writer.writerow([
            metric['label'],
            metric['formatted_a'],
            metric['formatted_b'],
            metric['formatted_diff'],
            trend_display
        ])
    
    # Generate response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = (
        f'attachment; filename=comparison_{comparison["record_a_info"]["id"]}_'
        f'{comparison["record_b_info"]["id"]}_{datetime.now().strftime("%Y%m%d")}.csv'
    )
    
    return response


@analytics_bp.route('/api/latest-snapshot')
@login_required
def get_latest_snapshot():
    """
    API endpoint to get the latest health snapshot for dashboard cards.
    Returns JSON data for AJAX updates.
    """
    latest_record = MCURecord.query.filter_by(
        user_id=current_user.id
    ).join(HealthMetrics).order_by(
        MCURecord.mcu_date.desc()
    ).first()
    
    if not latest_record or not latest_record.health_metrics:
        return jsonify({
            'has_data': False,
            'message': 'No health metrics available'
        })
    
    metrics = latest_record.health_metrics
    classifications = classify_all_metrics(metrics)
    
    return jsonify({
        'has_data': True,
        'record_id': latest_record.id,
        'mcu_date': latest_record.mcu_date.isoformat() if latest_record.mcu_date else None,
        'patient_name': latest_record.patient_name,
        'metrics': {
            'bmi': metrics.bmi,
            'systolic_bp': metrics.systolic_bp,
            'diastolic_bp': metrics.diastolic_bp,
            'hba1c': metrics.hba1c,
            'ldl': metrics.ldl,
            'hdl': metrics.hdl,
            'weight_kg': metrics.weight_kg,
            'fasting_glucose': metrics.fasting_glucose,
            'total_cholesterol': metrics.total_cholesterol,
            'triglycerides': metrics.triglycerides
        },
        'classifications': {k: v.to_dict() for k, v in classifications.items()}
    })


@analytics_bp.route('/api/records/<int:record_id>/classifications')
@login_required
def get_record_classifications(record_id: int):
    """Get health classifications for a specific record."""
    record = MCURecord.query.filter_by(
        id=record_id, user_id=current_user.id
    ).first()
    
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    
    if not record.health_metrics:
        return jsonify({
            'has_data': False,
            'message': 'No health metrics for this record'
        })
    
    metrics = record.health_metrics
    classifications = classify_all_metrics(metrics)
    
    return jsonify({
        'has_data': True,
        'record_id': record_id,
        'classifications': {k: v.to_dict() for k, v in classifications.items()}
    })