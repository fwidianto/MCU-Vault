"""
MCU Record management routes (CRUD operations).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.mcu_record import MCURecord, UploadedFile
from app.models.health_metrics import HealthMetrics

records_bp = Blueprint('records', __name__)


# Validation ranges for health metrics
VALIDATION_RANGES = {
    'height_cm': {'min': 50, 'max': 250, 'name': 'Height'},
    'weight_kg': {'min': 1, 'max': 500, 'name': 'Weight'},
    'bmi': {'min': 5, 'max': 100, 'name': 'BMI'},
    'systolic_bp': {'min': 0, 'max': 300, 'name': 'Systolic BP'},
    'diastolic_bp': {'min': 0, 'max': 200, 'name': 'Diastolic BP'},
    'heart_rate': {'min': 0, 'max': 250, 'name': 'Heart Rate'},
    'fasting_glucose': {'min': 0, 'max': 600, 'name': 'Fasting Glucose'},
    'hba1c': {'min': 0, 'max': 20, 'name': 'HbA1c'},
    'total_cholesterol': {'min': 0, 'max': 600, 'name': 'Total Cholesterol'},
    'ldl': {'min': 0, 'max': 400, 'name': 'LDL'},
    'hdl': {'min': 0, 'max': 150, 'name': 'HDL'},
    'triglycerides': {'min': 0, 'max': 1000, 'name': 'Triglycerides'},
    'sgot': {'min': 0, 'max': 500, 'name': 'SGOT'},
    'sgpt': {'min': 0, 'max': 500, 'name': 'SGPT'},
    'creatinine': {'min': 0, 'max': 20, 'name': 'Creatinine'},
    'uric_acid': {'min': 0, 'max': 20, 'name': 'Uric Acid'}
}


def validate_health_metric(field_name, value):
    """Validate a single health metric field."""
    if value is None or value == '':
        return None  # Allow NULL values
    
    try:
        float_val = float(value)
        if field_name in VALIDATION_RANGES:
            ranges = VALIDATION_RANGES[field_name]
            if float_val < ranges['min'] or float_val > ranges['max']:
                return f"{ranges['name']} must be between {ranges['min']} and {ranges['max']}."
        return float_val
    except (ValueError, TypeError):
        return "Invalid number format."


@records_bp.route('/records')
@login_required
def list():
    """List all MCU records with optional search."""
    # Get search parameters
    search = request.args.get('search', '').strip()
    search_by = request.args.get('search_by', 'patient_name')
    status_filter = request.args.get('status', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    # Base query - only current user's records
    query = MCURecord.query.filter_by(user_id=current_user.id)
    
    # Apply search
    if search:
        if search_by == 'patient_name':
            query = query.filter(MCURecord.patient_name.ilike(f'%{search}%'))
        elif search_by == 'company':
            query = query.filter(MCURecord.company.ilike(f'%{search}%'))
        elif search_by == 'mcu_date':
            # Try to parse date
            try:
                search_date = datetime.strptime(search, '%Y-%m-%d').date()
                query = query.filter(MCURecord.mcu_date == search_date)
            except ValueError:
                flash('Invalid date format. Use YYYY-MM-DD.', 'warning')
    
    # Apply status filter
    if status_filter:
        query = query.filter(MCURecord.status == status_filter)
    
    # Apply sorting
    sort_column = getattr(MCURecord, sort_by, MCURecord.created_at)
    if sort_order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Paginate results
    page = request.args.get('page', 1, type=int)
    per_page = 15
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('records/list.html',
                           records=pagination.items,
                           pagination=pagination,
                           search=search,
                           search_by=search_by,
                           status_filter=status_filter,
                           sort_by=sort_by,
                           sort_order=sort_order)


@records_bp.route('/records/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new MCU record with optional health metrics."""
    if request.method == 'POST':
        patient_name = request.form.get('patient_name', '').strip()
        company = request.form.get('company', '').strip()
        mcu_date_str = request.form.get('mcu_date', '')
        status = request.form.get('status', 'pending')
        notes = request.form.get('notes', '').strip()
        
        # Validate required fields
        errors = []
        
        if not patient_name:
            errors.append('Patient name is required.')
        elif len(patient_name) > 200:
            errors.append('Patient name must not exceed 200 characters.')
        
        if not mcu_date_str:
            errors.append('MCU date is required.')
        
        # Parse date
        mcu_date = None
        if mcu_date_str:
            try:
                mcu_date = datetime.strptime(mcu_date_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append('Invalid date format. Use YYYY-MM-DD.')
        
        # Validate health metrics
        health_errors = []
        health_data = {}
        
        metric_fields = [
            'height_cm', 'weight_kg', 'bmi',
            'systolic_bp', 'diastolic_bp', 'heart_rate',
            'fasting_glucose', 'hba1c',
            'total_cholesterol', 'ldl', 'hdl', 'triglycerides',
            'sgot', 'sgpt',
            'creatinine', 'uric_acid'
        ]
        
        for field in metric_fields:
            value = request.form.get(field, '').strip()
            validated = validate_health_metric(field, value)
            if isinstance(validated, str):  # It's an error message
                health_errors.append(validated)
            else:
                health_data[field] = validated
        
        # Check if any health metrics were entered
        has_health_data = any(v is not None for v in health_data.values())
        
        # Doctor notes
        doctor_notes = request.form.get('doctor_notes', '').strip()
        
        if health_errors:
            errors.extend(health_errors)
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('records/create.html',
                                   patient_name=patient_name,
                                   company=company,
                                   mcu_date=mcu_date_str,
                                   status=status,
                                   notes=notes,
                                   health_data=health_data,
                                   doctor_notes=doctor_notes)
        
        # Create record
        record = MCURecord(
            patient_name=patient_name,
            company=company or None,
            mcu_date=mcu_date,
            status=status,
            notes=notes or None,
            user_id=current_user.id
        )
        
        db.session.add(record)
        db.session.flush()  # Get the record ID
        
        # Create health metrics if any data was provided
        if has_health_data or doctor_notes:
            metrics = HealthMetrics(
                mcu_record_id=record.id,
                doctor_notes=doctor_notes or None,
                **health_data
            )
            db.session.add(metrics)
            
            # Auto-calculate BMI if height and weight provided
            if metrics.height_cm and metrics.weight_kg:
                metrics.calculate_bmi()
        
        db.session.commit()
        
        flash(f'MCU record for {patient_name} created successfully!', 'success')
        return redirect(url_for('records.detail', record_id=record.id))
    
    return render_template('records/create.html')


@records_bp.route('/records/<int:record_id>')
@login_required
def detail(record_id):
    """View MCU record details with health metrics."""
    record = MCURecord.query.filter_by(id=record_id, user_id=current_user.id).first()
    
    if not record:
        flash('Record not found.', 'danger')
        return redirect(url_for('records.list'))
    
    # Get associated files
    files = record.files.all()
    
    # Get health metrics (if exists)
    health_metrics = record.health_metrics
    
    return render_template('records/detail.html', record=record, files=files, health_metrics=health_metrics)


@records_bp.route('/records/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(record_id):
    """Edit an existing MCU record with health metrics."""
    record = MCURecord.query.filter_by(id=record_id, user_id=current_user.id).first()
    
    if not record:
        flash('Record not found.', 'danger')
        return redirect(url_for('records.list'))
    
    if request.method == 'POST':
        patient_name = request.form.get('patient_name', '').strip()
        company = request.form.get('company', '').strip()
        mcu_date_str = request.form.get('mcu_date', '')
        status = request.form.get('status', 'pending')
        notes = request.form.get('notes', '').strip()
        
        # Validate required fields
        errors = []
        
        if not patient_name:
            errors.append('Patient name is required.')
        elif len(patient_name) > 200:
            errors.append('Patient name must not exceed 200 characters.')
        
        if not mcu_date_str:
            errors.append('MCU date is required.')
        
        # Parse date
        mcu_date = None
        if mcu_date_str:
            try:
                mcu_date = datetime.strptime(mcu_date_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append('Invalid date format. Use YYYY-MM-DD.')
        
        # Validate health metrics
        health_errors = []
        health_data = {}
        
        metric_fields = [
            'height_cm', 'weight_kg', 'bmi',
            'systolic_bp', 'diastolic_bp', 'heart_rate',
            'fasting_glucose', 'hba1c',
            'total_cholesterol', 'ldl', 'hdl', 'triglycerides',
            'sgot', 'sgpt',
            'creatinine', 'uric_acid'
        ]
        
        for field in metric_fields:
            value = request.form.get(field, '').strip()
            validated = validate_health_metric(field, value)
            if isinstance(validated, str):  # It's an error message
                health_errors.append(validated)
            else:
                health_data[field] = validated
        
        # Doctor notes
        doctor_notes = request.form.get('doctor_notes', '').strip()
        
        if health_errors:
            errors.extend(health_errors)
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('records/edit.html', record=record)
        
        # Update record
        record.patient_name = patient_name
        record.company = company or None
        record.mcu_date = mcu_date
        record.status = status
        record.notes = notes or None
        record.updated_at = datetime.utcnow()
        
        # Update or create health metrics
        has_health_data = any(v is not None for v in health_data.values())
        
        if has_health_data or doctor_notes:
            if record.health_metrics:
                # Update existing
                metrics = record.health_metrics
                for key, value in health_data.items():
                    setattr(metrics, key, value)
                metrics.doctor_notes = doctor_notes or None
                
                # Auto-calculate BMI if height and weight provided
                if metrics.height_cm and metrics.weight_kg:
                    metrics.calculate_bmi()
            else:
                # Create new
                metrics = HealthMetrics(
                    mcu_record_id=record.id,
                    doctor_notes=doctor_notes or None,
                    **health_data
                )
                db.session.add(metrics)
                
                # Auto-calculate BMI if height and weight provided
                if metrics.height_cm and metrics.weight_kg:
                    metrics.calculate_bmi()
        
        db.session.commit()
        
        flash(f'Record for {patient_name} updated successfully!', 'success')
        return redirect(url_for('records.detail', record_id=record.id))
    
    return render_template('records/edit.html', record=record)


@records_bp.route('/records/<int:record_id>/delete', methods=['POST'])
@login_required
def delete(record_id):
    """Delete an MCU record."""
    record = MCURecord.query.filter_by(id=record_id, user_id=current_user.id).first()
    
    if not record:
        flash('Record not found.', 'danger')
        return redirect(url_for('records.list'))
    
    patient_name = record.patient_name
    
    # Delete associated files from filesystem
    import os
    from flask import current_app
    
    for file in record.files:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Delete record (cascades to files)
    db.session.delete(record)
    db.session.commit()
    
    flash(f'Record for {patient_name} deleted successfully.', 'success')
    return redirect(url_for('records.list'))


@records_bp.route('/api/records/<int:record_id>')
@login_required
def api_detail(record_id):
    """API endpoint for getting record details as JSON."""
    record = MCURecord.query.filter_by(id=record_id, user_id=current_user.id).first()
    
    if not record:
        return {'error': 'Record not found'}, 404
    
    return record.to_dict()