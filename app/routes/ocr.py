"""
OCR Routes for MCU Vault - Phase 2C

Handles file upload, OCR extraction, review workflow, and record creation.
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.mcu_record import MCURecord, UploadedFile
from app.models.health_metrics import HealthMetrics
from app.services.ocr_service import ocr_service, OCRResult
from app.services.ocr_mapping import mapper, extract_health_metrics

ocr_bp = Blueprint('ocr', __name__, url_prefix='/ocr')


# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_folder():
    """Get the upload folder path."""
    upload_folder = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'static', 'uploads', 'ocr'
    )
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder


@ocr_bp.route('/')
@login_required
def index():
    """OCR upload page."""
    return render_template('ocr/upload.html')


@ocr_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    """Handle file upload and OCR extraction."""
    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('ocr.index'))
    
    files = request.files.getlist('file')
    
    if not files or all(f.filename == '' for f in files):
        flash('No files selected.', 'danger')
        return redirect(url_for('ocr.index'))
    
    # Store results in session for review
    results = []
    errors = []
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            try:
                # Save file temporarily
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(get_upload_folder(), unique_filename)
                file.save(filepath)
                
                # Perform OCR
                ocr_result = ocr_service.extract(filepath)
                
                # Extract health metrics from OCR text
                extracted_data = extract_health_metrics(ocr_result.text)
                
                results.append({
                    'filename': filename,
                    'filepath': filepath,
                    'ocr_result': ocr_result,
                    'extracted_data': extracted_data
                })
                
            except Exception as e:
                errors.append({
                    'filename': file.filename,
                    'error': str(e)
                })
        else:
            errors.append({
                'filename': file.filename if file else 'Unknown',
                'error': 'Unsupported file type. Allowed: PDF, JPG, JPEG, PNG'
            })
    
    if not results:
        for err in errors:
            flash(f"Failed to process {err['filename']}: {err['error']}", 'danger')
        return redirect(url_for('ocr.index'))
    
    # Store results in session for review
    session['ocr_results'] = results
    session['ocr_errors'] = errors
    
    return redirect(url_for('ocr.review'))


@ocr_bp.route('/review')
@login_required
def review():
    """Review extracted data before saving."""
    results = session.get('ocr_results', [])
    errors = session.get('ocr_errors', [])
    
    if not results:
        flash('No extraction results to review.', 'info')
        return redirect(url_for('ocr.index'))
    
    return render_template('ocr/review.html', results=results, errors=errors)


@ocr_bp.route('/update_field', methods=['POST'])
@login_required
def update_field():
    """Update a single extracted field value."""
    data = request.get_json()
    
    index = data.get('index')
    field = data.get('field')
    value = data.get('value')
    
    results = session.get('ocr_results', [])
    
    if index is not None and index < len(results):
        if value is not None and value != '':
            try:
                results[index]['extracted_data'][field] = {
                    'value': float(value),
                    'confidence': 100.0,  # User-entered value has 100% confidence
                    'manual': True
                }
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid number'}), 400
        elif field in results[index]['extracted_data']:
            del results[index]['extracted_data'][field]
        
        session['ocr_results'] = results
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid index'}), 400


@ocr_bp.route('/save', methods=['POST'])
@login_required
def save():
    """Save extracted data as MCU records."""
    results = session.get('ocr_results', [])
    
    if not results:
        flash('No data to save.', 'danger')
        return redirect(url_for('ocr.index'))
    
    saved_count = 0
    errors = []
    
    for i, result in enumerate(results):
        try:
            # Get user-modified data
            form_key = f'include_{i}'
            if form_key not in request.form:
                continue
            
            extracted_data = result['extracted_data']
            
            # Extract metadata
            patient_name = extracted_data.get('patient_name', {}).get('value', 'Unknown Patient')
            mcu_date_str = extracted_data.get('mcu_date', {}).get('value')
            company = extracted_data.get('company', {}).get('value', '')
            
            # Parse date if available
            mcu_date = datetime.now().date()
            if mcu_date_str:
                try:
                    for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%m-%d-%Y', '%m/%d/%Y']:
                        try:
                            mcu_date = datetime.strptime(mcu_date_str, fmt).date()
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass
            
            # Create MCU record
            record = MCURecord(
                patient_name=patient_name,
                company=company,
                mcu_date=mcu_date,
                status='pending',
                notes='Created from OCR extraction',
                user_id=current_user.id
            )
            db.session.add(record)
            db.session.flush()
            
            # Create health metrics
            metrics = HealthMetrics(mcu_record_id=record.id)
            
            # Map extracted fields to health metrics
            field_mapping = {
                'height_cm': 'height_cm',
                'weight_kg': 'weight_kg',
                'bmi': 'bmi',
                'systolic_bp': 'systolic_bp',
                'diastolic_bp': 'diastolic_bp',
                'heart_rate': 'heart_rate',
                'fasting_glucose': 'fasting_glucose',
                'hba1c': 'hba1c',
                'total_cholesterol': 'total_cholesterol',
                'ldl': 'ldl',
                'hdl': 'hdl',
                'triglycerides': 'triglycerides',
                'sgot': 'sgot',
                'sgpt': 'sgpt',
                'creatinine': 'creatinine',
                'uric_acid': 'uric_acid',
            }
            
            for ocr_field, model_field in field_mapping.items():
                if ocr_field in extracted_data:
                    value = extracted_data[ocr_field].get('value')
                    if value is not None:
                        setattr(metrics, model_field, value)
            
            # Calculate BMI if not provided
            if metrics.height_cm and metrics.weight_kg and not metrics.bmi:
                metrics.calculate_bmi()
            
            db.session.add(metrics)
            
            # Attach original file
            if os.path.exists(result['filepath']):
                original_filename = result['filename']
                stored_filename = os.path.basename(result['filepath'])
                file_size = os.path.getsize(result['filepath'])
                
                uploaded_file = UploadedFile(
                    filename=stored_filename,
                    original_filename=original_filename,
                    file_type=original_filename.rsplit('.', 1)[1].lower(),
                    file_size=file_size,
                    mcu_record_id=record.id
                )
                db.session.add(uploaded_file)
            
            db.session.commit()
            saved_count += 1
            
        except Exception as e:
            db.session.rollback()
            errors.append({
                'filename': result.get('filename', f'Record {i+1}'),
                'error': str(e)
            })
    
    # Clear session
    session.pop('ocr_results', None)
    session.pop('ocr_errors', None)
    
    if saved_count > 0:
        flash(f'Successfully saved {saved_count} MCU record(s).', 'success')
    
    for err in errors:
        flash(f"Failed to save {err['filename']}: {err['error']}", 'warning')
    
    return redirect(url_for('records.list'))


@ocr_bp.route('/cancel', methods=['POST'])
@login_required
def cancel():
    """Cancel OCR workflow and clean up temp files."""
    results = session.get('ocr_results', [])
    
    # Clean up temp files
    for result in results:
        filepath = result.get('filepath')
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
    
    session.pop('ocr_results', None)
    session.pop('ocr_errors', None)
    
    flash('OCR processing cancelled.', 'info')
    return redirect(url_for('ocr.index'))


@ocr_bp.route('/status')
@login_required
def status():
    """Check OCR service availability."""
    return jsonify({
        'ocr_available': ocr_service.is_available(),
        'tesseract_version': ocr_service.tesseract_available,
        'poppler_version': ocr_service.poppler_available
    })


@ocr_bp.route('/bulk')
@login_required
def bulk():
    """Bulk import page."""
    return render_template('ocr/bulk.html')


@ocr_bp.route('/bulk/upload', methods=['POST'])
@login_required
def bulk_upload():
    """Handle bulk file upload for batch processing."""
    if 'files' not in request.files:
        flash('No files selected.', 'danger')
        return redirect(url_for('ocr.bulk'))
    
    files = request.files.getlist('files')
    
    if not files or all(f.filename == '' for f in files):
        flash('No files selected.', 'danger')
        return redirect(url_for('ocr.bulk'))
    
    # Process files
    file_jobs = []
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(get_upload_folder(), unique_filename)
                file.save(filepath)
                
                file_jobs.append({
                    'id': unique_filename,
                    'filename': filename,
                    'filepath': filepath,
                    'status': 'pending',
                    'result': None
                })
            except Exception as e:
                flash(f"Failed to process {file.filename}: {str(e)}", 'danger')
    
    if not file_jobs:
        flash('No valid files to process.', 'danger')
        return redirect(url_for('ocr.bulk'))
    
    # Store in session for batch processing
    session['bulk_jobs'] = file_jobs
    
    return redirect(url_for('ocr.bulk_progress'))


@ocr_bp.route('/bulk/progress')
@login_required
def bulk_progress():
    """Show bulk processing progress."""
    jobs = session.get('bulk_jobs', [])
    
    if not jobs:
        flash('No bulk jobs to process.', 'info')
        return redirect(url_for('ocr.bulk'))
    
    return render_template('ocr/bulk_progress.html', jobs=jobs)


@ocr_bp.route('/bulk/process/<job_id>')
@login_required
def bulk_process(job_id):
    """Process a single bulk job."""
    jobs = session.get('bulk_jobs', [])
    
    job = next((j for j in jobs if j['id'] == job_id), None)
    
    if not job:
        return jsonify({'success': False, 'error': 'Job not found'}), 404
    
    if job['status'] != 'pending':
        return jsonify({'success': True, 'status': job['status']})
    
    try:
        # Perform OCR
        ocr_result = ocr_service.extract(job['filepath'])
        
        if ocr_result.success:
            # Extract health metrics
            extracted_data = extract_health_metrics(ocr_result.text)
            job['status'] = 'completed'
            job['result'] = {
                'ocr': ocr_result.to_dict(),
                'extracted': extracted_data
            }
        else:
            job['status'] = 'failed'
            job['error'] = ocr_result.error_message
        
        session['bulk_jobs'] = jobs
        return jsonify({'success': True, 'status': job['status']})
        
    except Exception as e:
        job['status'] = 'failed'
        job['error'] = str(e)
        session['bulk_jobs'] = jobs
        return jsonify({'success': False, 'error': str(e)}), 500


@ocr_bp.route('/bulk/save', methods=['POST'])
@login_required
def bulk_save():
    """Save bulk processed results as MCU records."""
    jobs = session.get('bulk_jobs', [])
    
    saved_count = 0
    errors = []
    
    for job in jobs:
        if job['status'] != 'completed' or not job.get('result'):
            continue
        
        try:
            result = job['result']
            extracted_data = result.get('extracted', {})
            
            # Extract metadata
            patient_name = extracted_data.get('patient_name', {}).get('value', 'Unknown Patient')
            company = extracted_data.get('company', {}).get('value', '')
            
            # Create MCU record
            record = MCURecord(
                patient_name=patient_name,
                company=company,
                mcu_date=datetime.now().date(),
                status='pending',
                notes='Created from bulk OCR import',
                user_id=current_user.id
            )
            db.session.add(record)
            db.session.flush()
            
            # Create health metrics
            metrics = HealthMetrics(mcu_record_id=record.id)
            
            field_mapping = {
                'height_cm': 'height_cm',
                'weight_kg': 'weight_kg',
                'bmi': 'bmi',
                'systolic_bp': 'systolic_bp',
                'diastolic_bp': 'diastolic_bp',
                'heart_rate': 'heart_rate',
                'fasting_glucose': 'fasting_glucose',
                'hba1c': 'hba1c',
                'total_cholesterol': 'total_cholesterol',
                'ldl': 'ldl',
                'hdl': 'hdl',
                'triglycerides': 'triglycerides',
                'sgot': 'sgot',
                'sgpt': 'sgpt',
                'creatinine': 'creatinine',
                'uric_acid': 'uric_acid',
            }
            
            for ocr_field, model_field in field_mapping.items():
                if ocr_field in extracted_data:
                    value = extracted_data[ocr_field].get('value')
                    if value is not None:
                        setattr(metrics, model_field, value)
            
            if metrics.height_cm and metrics.weight_kg and not metrics.bmi:
                metrics.calculate_bmi()
            
            db.session.add(metrics)
            
            # Attach file
            if os.path.exists(job['filepath']):
                original_filename = job['filename']
                stored_filename = os.path.basename(job['filepath'])
                file_size = os.path.getsize(job['filepath'])
                
                uploaded_file = UploadedFile(
                    filename=stored_filename,
                    original_filename=original_filename,
                    file_type=original_filename.rsplit('.', 1)[1].lower(),
                    file_size=file_size,
                    mcu_record_id=record.id
                )
                db.session.add(uploaded_file)
            
            db.session.commit()
            saved_count += 1
            
        except Exception as e:
            db.session.rollback()
            errors.append({
                'filename': job['filename'],
                'error': str(e)
            })
    
    session.pop('bulk_jobs', None)
    
    if saved_count > 0:
        flash(f'Successfully saved {saved_count} MCU record(s).', 'success')
    
    for err in errors:
        flash(f"Failed to save {err['filename']}: {err['error']}", 'warning')
    
    return redirect(url_for('records.list'))