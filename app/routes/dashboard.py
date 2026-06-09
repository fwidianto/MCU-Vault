"""
Dashboard routes for displaying user statistics and recent activity.
"""
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from app import db
from app.models.mcu_record import MCURecord, UploadedFile
from app.models.health_metrics import HealthMetrics

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Display the main dashboard with statistics."""
    # Get statistics
    total_records = MCURecord.query.filter_by(user_id=current_user.id).count()
    
    # Records by status
    status_counts = db.session.query(
        MCURecord.status, 
        func.count(MCURecord.id)
    ).filter(
        MCURecord.user_id == current_user.id
    ).group_by(MCURecord.status).all()
    
    status_dict = {status: count for status, count in status_counts}
    
    # Total files
    total_files = db.session.query(func.count(UploadedFile.id)).join(
        MCURecord
    ).filter(
        MCURecord.user_id == current_user.id
    ).scalar() or 0
    
    # Recent records (last 5)
    recent_records = MCURecord.query.filter_by(
        user_id=current_user.id
    ).order_by(
        MCURecord.created_at.desc()
    ).limit(5).all()
    
    # Records this month
    first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    records_this_month = MCURecord.query.filter(
        MCURecord.user_id == current_user.id,
        MCURecord.created_at >= first_day_of_month
    ).count()
    
    # Calculate user statistics
    member_since = current_user.created_at
    
    # Get records trend (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    records_last_week = MCURecord.query.filter(
        MCURecord.user_id == current_user.id,
        MCURecord.created_at >= seven_days_ago
    ).count()
    
    # Health Metrics Statistics (Phase 2A)
    # Count records with health metrics
    records_with_metrics = db.session.query(func.count(HealthMetrics.id)).join(
        MCURecord
    ).filter(
        MCURecord.user_id == current_user.id
    ).scalar() or 0
    
    # Records without health metrics
    records_without_metrics = total_records - records_with_metrics
    
    context = {
        'total_records': total_records,
        'total_files': total_files,
        'records_this_month': records_this_month,
        'records_last_week': records_last_week,
        'member_since': member_since,
        'status_counts': status_dict,
        'recent_records': recent_records,
        'pending_count': status_dict.get('pending', 0),
        'cleared_count': status_dict.get('cleared', 0),
        'not_cleared_count': status_dict.get('not-cleared', 0),
        'follow_up_count': status_dict.get('needs-follow-up', 0),
        # Health metrics statistics
        'records_with_metrics': records_with_metrics,
        'records_without_metrics': records_without_metrics
    }
    
    return render_template('dashboard.html', **context)


@dashboard_bp.route('/api/dashboard/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics (for AJAX refresh)."""
    total_records = MCURecord.query.filter_by(user_id=current_user.id).count()
    total_files = db.session.query(func.count(UploadedFile.id)).join(
        MCURecord
    ).filter(MCURecord.user_id == current_user.id).scalar() or 0
    
    # Records by status
    status_counts = db.session.query(
        MCURecord.status, 
        func.count(MCURecord.id)
    ).filter(MCURecord.user_id == current_user.id).group_by(MCURecord.status).all()
    
    return {
        'total_records': total_records,
        'total_files': total_files,
        'status_counts': dict(status_counts)
    }