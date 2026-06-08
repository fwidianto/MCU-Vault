"""
File upload routes for MCU records.
"""
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.mcu_record import MCURecord, UploadedFile
from app.utils.helpers import allowed_file, get_file_type, generate_unique_filename, get_mime_type

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/records/<int:record_id>/upload', methods=['GET', 'POST'])
@login_required
def upload_file(record_id):
    """Upload files to an MCU record."""
    record = MCURecord.query.filter_by(id=record_id, user_id=current_user.id).first()
    
    if not record:
        flash('Record not found.', 'danger')
        return redirect(url_for('records.list'))
    
    if request.method == 'POST':
        # Check if files were selected
        if 'files' not in request.files:
            flash('No files selected.', 'warning')
            return redirect(url_for('upload.upload_file', record_id=record_id))
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            flash('No files selected.', 'warning')
            return redirect(url_for('upload.upload_file', record_id=record_id))
        
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'jpg', 'jpeg', 'png'})
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        
        uploaded_count = 0
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
            
            # Check file extension
            if not allowed_file(file.filename, allowed_extensions):
                errors.append(f"'{file.filename}' has an unsupported file type.")
                continue
            
            # Get file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            # Check file size
            if file_size > max_size:
                errors.append(f"'{file.filename}' exceeds the maximum file size (16MB).")
                continue
            
            # Generate unique filename and save
            original_filename = secure_filename(file.filename)
            unique_filename = generate_unique_filename(original_filename)
            file_path = os.path.join(upload_folder, unique_filename)
            
            try:
                file.save(file_path)
                
                # Determine file type
                file_type = get_file_type(original_filename)
                mime_type = get_mime_type(original_filename)
                
                # Create database record
                uploaded_file = UploadedFile(
                    filename=unique_filename,
                    original_filename=original_filename,
                    file_type=file_type,
                    file_size=file_size,
                    mime_type=mime_type,
                    mcu_record_id=record_id
                )
                
                db.session.add(uploaded_file)
                uploaded_count += 1
                
            except Exception as e:
                errors.append(f"Failed to upload '{original_filename}': {str(e)}")
                # Clean up file if it was saved
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        db.session.commit()
        
        if uploaded_count > 0:
            flash(f'{uploaded_count} file(s) uploaded successfully!', 'success')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
        
        return redirect(url_for('records.detail', record_id=record_id))
    
    # Get existing files
    files = record.files.all()
    
    return render_template('upload.html', record=record, files=files)


@upload_bp.route('/records/<int:record_id>/files/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(record_id, file_id):
    """Delete an uploaded file."""
    record = MCURecord.query.filter_by(id=record_id, user_id=current_user.id).first()
    
    if not record:
        flash('Record not found.', 'danger')
        return redirect(url_for('records.list'))
    
    uploaded_file = UploadedFile.query.filter_by(id=file_id, mcu_record_id=record_id).first()
    
    if not uploaded_file:
        flash('File not found.', 'danger')
        return redirect(url_for('records.detail', record_id=record_id))
    
    # Delete file from filesystem
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
    file_path = os.path.join(upload_folder, uploaded_file.filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
    
    filename = uploaded_file.original_filename
    
    # Delete database record
    db.session.delete(uploaded_file)
    db.session.commit()
    
    flash(f"File '{filename}' deleted successfully.", 'success')
    return redirect(url_for('records.detail', record_id=record_id))


@upload_bp.route('/files/')
@login_required
def serve_file(filename):
    """Serve an uploaded file."""
    # Find file in database
    uploaded_file = UploadedFile.query.filter_by(filename=filename).first()
    
    if not uploaded_file:
        flash('File not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Verify user owns the record
    record = MCURecord.query.filter_by(id=uploaded_file.mcu_record_id, user_id=current_user.id).first()
    
    if not record:
        flash('You do not have permission to access this file.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    from flask import send_from_directory
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
    
    return send_from_directory(upload_folder, filename, as_attachment=False,
                               download_name=uploaded_file.original_filename)


@upload_bp.route('/files//download')
@login_required
def download_file(filename):
    """Download an uploaded file."""
    uploaded_file = UploadedFile.query.filter_by(filename=filename).first()
    
    if not uploaded_file:
        flash('File not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    record = MCURecord.query.filter_by(id=uploaded_file.mcu_record_id, user_id=current_user.id).first()
    
    if not record:
        flash('You do not have permission to access this file.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    from flask import send_from_directory
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
    
    return send_from_directory(upload_folder, filename, as_attachment=True,
                               download_name=uploaded_file.original_filename)