"""
MCU Record management routes (CRUD operations).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.mcu_record import MCURecord, UploadedFile

records_bp = Blueprint('records', __name__)


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
    """Create a new MCU record."""
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
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('records/create.html',
                                   patient_name=patient_name,
                                   company=company,
                                   mcu_date=mcu_date_str,
                                   status=status,
                                   notes=notes)
        
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
        db.session.commit()
        
        flash(f'MCU record for {patient_name} created successfully!', 'success')
        return redirect(url_for('records.detail', record_id=record.id))
    
    return render_template('records/create.html')


@records_bp.route('/records/<int:record_id>')
@login_required
def detail(record_id):
    """View MCU record details."""
    record = MCURecord.query.filter_by(id=record_id, user_id=current_user.id).first()
    
    if not record:
        flash('Record not found.', 'danger')
        return redirect(url_for('records.list'))
    
    # Get associated files
    files = record.files.all()
    
    return render_template('records/detail.html', record=record, files=files)


@records_bp.route('/records/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(record_id):
    """Edit an existing MCU record."""
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