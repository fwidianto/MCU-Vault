"""
AI Health Intelligence Routes for Phase 3A.
Provides endpoints for AI-generated health insights.
"""
from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required, current_user
from datetime import datetime
import logging

from app import db
from app.models.mcu_record import MCURecord
from app.models.health_metrics import HealthMetrics
from app.services.health_intelligence import (
    get_health_intelligence_service,
    HealthIntelligenceService
)
from app.utils.health_classification import classify_all_metrics

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')


def metrics_to_dict(metrics: HealthMetrics) -> dict:
    """Convert HealthMetrics object to dictionary."""
    if not metrics:
        return {}
    return {
        'height_cm': metrics.height_cm,
        'weight_kg': metrics.weight_kg,
        'bmi': metrics.bmi,
        'systolic_bp': metrics.systolic_bp,
        'diastolic_bp': metrics.diastolic_bp,
        'heart_rate': metrics.heart_rate,
        'fasting_glucose': metrics.fasting_glucose,
        'hba1c': metrics.hba1c,
        'total_cholesterol': metrics.total_cholesterol,
        'ldl': metrics.ldl,
        'hdl': metrics.hdl,
        'triglycerides': metrics.triglycerides,
        'sgot': metrics.sgot,
        'sgpt': metrics.sgpt,
        'creatinine': metrics.creatinine,
        'uric_acid': metrics.uric_acid,
    }


def get_record_metrics(record: MCURecord) -> dict:
    """Get metrics dict from a record, with classifications."""
    metrics = metrics_to_dict(record.health_metrics)
    if record.health_metrics:
        classifications = classify_all_metrics(record.health_metrics)
        metrics['_classifications'] = {k: v.to_dict() for k, v in classifications.items()}
    return metrics


@ai_bp.route('/')
@login_required
def index():
    """AI Health Intelligence main page."""
    service = get_health_intelligence_service()
    status = service.get_status()
    
    # Get user's records for context
    records = MCURecord.query.filter_by(user_id=current_user.id)\
        .order_by(MCURecord.mcu_date.desc())\
        .limit(10)\
        .all()
    
    return render_template('ai/index.html',
                         ai_status=status,
                         recent_records=records)


@ai_bp.route('/status')
@login_required
def status():
    """Get AI service status."""
    service = get_health_intelligence_service()
    return jsonify(service.get_status())


@ai_bp.route('/summary/<int:record_id>')
@login_required
def get_summary(record_id: int):
    """
    Generate AI summary for a specific MCU record.
    
    Returns JSON with success status and summary text.
    """
    # Verify record belongs to current user
    record = MCURecord.query.filter_by(
        id=record_id, 
        user_id=current_user.id
    ).first()
    
    if not record:
        return jsonify({
            'success': False,
            'error': 'Record not found'
        }), 404
    
    # Get metrics
    metrics = get_record_metrics(record)
    if not any(metrics.values()):
        return jsonify({
            'success': False,
            'error': 'No health metrics available for this record'
        }), 400
    
    # Generate summary
    service = get_health_intelligence_service()
    result = service.generate_summary(
        patient_name=record.patient_name,
        metrics=metrics,
        record_date=record.mcu_date.strftime('%B %d, %Y')
    )
    
    return jsonify(result)


@ai_bp.route('/compare')
@login_required
def compare():
    """Page for comparing two MCU records with AI."""
    service = get_health_intelligence_service()
    status = service.get_status()
    
    # Get user's records
    records = MCURecord.query.filter_by(user_id=current_user.id)\
        .order_by(MCURecord.mcu_date.desc())\
        .all()
    
    return render_template('ai/compare.html',
                         ai_status=status,
                         records=records)


@ai_bp.route('/comparison', methods=['POST'])
@login_required
def get_comparison():
    """
    Generate AI comparison between two MCU records.
    
    Expects JSON with 'current_id' and 'previous_id'.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    current_id = data.get('current_id')
    previous_id = data.get('previous_id')
    
    if not current_id or not previous_id:
        return jsonify({
            'success': False,
            'error': 'Both current_id and previous_id are required'
        }), 400
    
    # Verify records belong to current user
    current_record = MCURecord.query.filter_by(
        id=current_id, 
        user_id=current_user.id
    ).first()
    
    previous_record = MCURecord.query.filter_by(
        id=previous_id, 
        user_id=current_user.id
    ).first()
    
    if not current_record or not previous_record:
        return jsonify({
            'success': False,
            'error': 'One or both records not found'
        }), 404
    
    # Get metrics
    current_metrics = get_record_metrics(current_record)
    previous_metrics = get_record_metrics(previous_record)
    
    if not any(current_metrics.values()):
        return jsonify({
            'success': False,
            'error': 'No health metrics available for current record'
        }), 400
    
    if not any(previous_metrics.values()):
        return jsonify({
            'success': False,
            'error': 'No health metrics available for previous record'
        }), 400
    
    # Generate comparison
    service = get_health_intelligence_service()
    result = service.generate_comparison(
        patient_name=current_record.patient_name,
        current=current_metrics,
        previous=previous_metrics,
        current_date=current_record.mcu_date.strftime('%B %d, %Y'),
        previous_date=previous_record.mcu_date.strftime('%B %d, %Y')
    )
    
    return jsonify(result)


@ai_bp.route('/trends')
@login_required
def trends():
    """Page for AI trend analysis."""
    service = get_health_intelligence_service()
    status = service.get_status()
    
    # Get user's records
    records = MCURecord.query.filter_by(user_id=current_user.id)\
        .order_by(MCURecord.mcu_date.asc())\
        .all()
    
    return render_template('ai/trends.html',
                         ai_status=status,
                         records=records)


@ai_bp.route('/trend-analysis', methods=['POST'])
@login_required
def get_trend_analysis():
    """
    Generate AI trend analysis from multiple MCU records.
    
    Expects JSON with optional 'record_ids' (list) or uses all user's records.
    """
    data = request.get_json() or {}
    record_ids = data.get('record_ids', [])
    
    # Get records
    query = MCURecord.query.filter_by(user_id=current_user.id)
    
    if record_ids:
        query = query.filter(MCURecord.id.in_(record_ids))
    
    records = query.order_by(MCURecord.mcu_date.asc()).all()
    
    if len(records) < 2:
        return jsonify({
            'success': False,
            'error': 'At least 2 MCU records are needed for trend analysis'
        }), 400
    
    # Format records for analysis
    formatted_records = []
    years = set()
    
    for record in records:
        years.add(record.mcu_date.year)
        formatted_records.append({
            'date': record.mcu_date.strftime('%B %d, %Y'),
            'metrics': get_record_metrics(record)
        })
    
    # Generate analysis
    service = get_health_intelligence_service()
    result = service.generate_trend_analysis(
        patient_name=records[0].patient_name if records else 'Patient',
        records=formatted_records,
        start_year=min(years) if years else datetime.now().year,
        end_year=max(years) if years else datetime.now().year
    )
    
    return jsonify(result)


@ai_bp.route('/timeline')
@login_required
def timeline():
    """Page for AI health timeline narrative."""
    service = get_health_intelligence_service()
    status = service.get_status()
    
    # Get user's records
    records = MCURecord.query.filter_by(user_id=current_user.id)\
        .order_by(MCURecord.mcu_date.asc())\
        .all()
    
    return render_template('ai/timeline.html',
                         ai_status=status,
                         records=records)


@ai_bp.route('/health-timeline', methods=['POST'])
@login_required
def get_health_timeline():
    """
    Generate AI health timeline narrative.
    
    Expects JSON with optional 'record_ids'.
    """
    data = request.get_json() or {}
    record_ids = data.get('record_ids', [])
    
    # Get records
    query = MCURecord.query.filter_by(user_id=current_user.id)
    
    if record_ids:
        query = query.filter(MCURecord.id.in_(record_ids))
    
    records = query.order_by(MCURecord.mcu_date.asc()).all()
    
    if len(records) < 2:
        return jsonify({
            'success': False,
            'error': 'At least 2 MCU records are needed for timeline generation'
        }), 400
    
    # Generate period summaries based on years
    years = sorted(set(r.mcu_date.year for r in records))
    summary_by_period = {}
    
    for year in years:
        year_records = [r for r in records if r.mcu_date.year == year]
        if year_records:
            period = f"Year {year}"
            count = len(year_records)
            summary_by_period[period] = f"{count} MCU record(s)"
    
    # Format records for timeline
    formatted_records = []
    for record in records:
        formatted_records.append({
            'date': record.mcu_date.strftime('%B %d, %Y'),
            'metrics': get_record_metrics(record)
        })
    
    # Generate timeline
    service = get_health_intelligence_service()
    result = service.generate_timeline(
        patient_name=records[0].patient_name if records else 'Patient',
        records=formatted_records,
        summary_by_period=summary_by_period
    )
    
    return jsonify(result)


@ai_bp.route('/explain/<metric_name>')
@login_required
def explain_metric(metric_name: str):
    """
    Get AI explanation for a specific health metric.
    
    Optional query param: 'value' for the patient's specific value.
    """
    value = request.args.get('value', type=float)
    
    service = get_health_intelligence_service()
    result = service.explain_metric(metric_name, value)
    
    status_code = 200 if result['success'] else 500
    return jsonify(result), status_code


@ai_bp.route('/explain')
@login_required
def explain_list():
    """Get list of all explainable metrics."""
    from app.services.ai_prompts import get_all_explainable_metrics, get_metric_explanation
    
    metrics = get_all_explainable_metrics()
    explanations = {}
    
    for metric in metrics:
        info = get_metric_explanation(metric)
        if info:
            explanations[metric] = {
                'name': info.get('name', metric),
                'description': info.get('description', ''),
                'ranges': info.get('ranges', {}),
                'importance': info.get('importance', '')
            }
    
    return jsonify({
        'success': True,
        'metrics': explanations
    })


@ai_bp.route('/report/<int:record_id>')
@login_required
def generate_report(record_id: int):
    """
    Generate a downloadable AI health report for a record.
    
    Supports 'format' query param: 'pdf' (default).
    """
    from flask import make_response
    
    # Verify record belongs to current user
    record = MCURecord.query.filter_by(
        id=record_id, 
        user_id=current_user.id
    ).first()
    
    if not record:
        return jsonify({
            'success': False,
            'error': 'Record not found'
        }), 404
    
    format_type = request.args.get('format', 'pdf')
    service = get_health_intelligence_service()
    
    # Gather data for report
    metrics = get_record_metrics(record)
    
    if not any(metrics.values()):
        return jsonify({
            'success': False,
            'error': 'No health metrics available for this record'
        }), 400
    
    # Get previous record for comparison
    previous_record = MCURecord.query\
        .filter(
            MCURecord.user_id == current_user.id,
            MCURecord.id != record_id,
            MCURecord.mcu_date < record.mcu_date
        )\
        .order_by(MCURecord.mcu_date.desc())\
        .first()
    
    # Generate all AI content
    summary_result = service.generate_summary(
        patient_name=record.patient_name,
        metrics=metrics,
        record_date=record.mcu_date.strftime('%B %d, %Y')
    )
    
    comparison_result = None
    if previous_record:
        previous_metrics = get_record_metrics(previous_record)
        if any(previous_metrics.values()):
            comparison_result = service.generate_comparison(
                patient_name=record.patient_name,
                current=metrics,
                previous=previous_metrics,
                current_date=record.mcu_date.strftime('%B %d, %Y'),
                previous_date=previous_record.mcu_date.strftime('%B %d, %Y')
            )
    
    # Get all user's records for trends
    all_records = MCURecord.query\
        .filter_by(user_id=current_user.id)\
        .order_by(MCURecord.mcu_date.asc())\
        .all()
    
    trend_result = None
    if len(all_records) >= 2:
        formatted_records = [
            {'date': r.mcu_date.strftime('%B %d, %Y'), 'metrics': get_record_metrics(r)}
            for r in all_records
        ]
        trend_result = service.generate_trend_analysis(
            patient_name=record.patient_name,
            records=formatted_records,
            start_year=min(r.mcu_date.year for r in all_records),
            end_year=max(r.mcu_date.year for r in all_records)
        )
    
    # Generate report content
    report_content = generate_report_content(
        record=record,
        metrics=metrics,
        summary=summary_result.get('summary') if summary_result.get('success') else None,
        comparison=comparison_result.get('comparison') if comparison_result and comparison_result.get('success') else None,
        trends=trend_result.get('analysis') if trend_result and trend_result.get('success') else None
    )
    
    if format_type == 'pdf':
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.units import inch
            from io import BytesIO
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                   leftMargin=0.75*inch, rightMargin=0.75*inch,
                                   topMargin=0.75*inch, bottomMargin=0.75*inch)
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=20
            )
            
            content = []
            content.append(Paragraph("MCU Health Report", title_style))
            content.append(Spacer(1, 12))
            
            for section in report_content:
                if section['type'] == 'heading':
                    content.append(Paragraph(section['content'], styles['Heading2']))
                    content.append(Spacer(1, 12))
                elif section['type'] == 'text':
                    content.append(Paragraph(section['content'], styles['Normal']))
                    content.append(Spacer(1, 12))
            
            doc.build(content)
            
            buffer.seek(0)
            response = make_response(buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=MCU_Report_{record.mcu_date.strftime("%Y%m%d")}.pdf'
            
            return response
            
        except ImportError:
            # Fall back to text if reportlab not installed
            return jsonify({
                'success': False,
                'error': 'PDF generation requires reportlab package. Install with: pip install reportlab'
            }), 500
    else:
        # Return as formatted text
        return jsonify({
            'success': True,
            'content': report_content,
            'record_date': record.mcu_date.strftime('%B %d, %Y'),
            'patient_name': record.patient_name
        })


def generate_report_content(record, metrics, summary, comparison, trends) -> list:
    """Generate structured content for health report."""
    content = []
    
    # Header
    content.append({
        'type': 'heading',
        'content': f"Patient: {record.patient_name}"
    })
    content.append({
        'type': 'text',
        'content': f"MCU Date: {record.mcu_date.strftime('%B %d, %Y')}"
    })
    content.append({
        'type': 'text',
        'content': f"Company: {record.company or 'N/A'}"
    })
    
    # Summary
    content.append({
        'type': 'heading',
        'content': "Latest MCU Summary"
    })
    if summary:
        # Clean up HTML/markdown for text report
        clean_summary = summary.replace('**', '').replace('##', '')
        content.append({
            'type': 'text',
            'content': clean_summary
        })
    else:
        content.append({
            'type': 'text',
            'content': "AI summary not available."
        })
    
    # Comparison
    if comparison:
        content.append({
            'type': 'heading',
            'content': "Historical Comparison"
        })
        clean_comparison = comparison.replace('**', '').replace('##', '')
        content.append({
            'type': 'text',
            'content': clean_comparison
        })
    
    # Trends
    if trends:
        content.append({
            'type': 'heading',
            'content': "Trend Analysis"
        })
        clean_trends = trends.replace('**', '').replace('##', '')
        content.append({
            'type': 'text',
            'content': clean_trends
        })
    
    # Disclaimer
    content.append({
        'type': 'heading',
        'content': "Medical Disclaimer"
    })
    content.append({
        'type': 'text',
        'content': "This report is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider regarding any medical concerns."
    })
    
    return content