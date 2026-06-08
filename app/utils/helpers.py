"""
Utility helper functions for MCU Vault.
"""
import os
import re
from datetime import datetime, date
from werkzeug.utils import secure_filename


def allowed_file(filename, allowed_extensions):
    """
    Check if a file has an allowed extension.
    
    Args:
        filename: Name of the file to check
        allowed_extensions: Set of allowed file extensions
    
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions


def get_file_type(filename):
    """
    Determine the file type category based on extension.
    
    Args:
        filename: Name of the file
    
    Returns:
        str: File type category ('pdf', 'image', or 'unknown')
    """
    if not filename or '.' not in filename:
        return 'unknown'
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext == 'pdf':
        return 'pdf'
    elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
        return 'image'
    else:
        return 'unknown'


def sanitize_filename(filename):
    """
    Sanitize a filename to prevent security issues.
    
    Args:
        filename: Original filename
    
    Returns:
        str: Sanitized filename
    """
    # Use Werkzeug's secure_filename
    safe_name = secure_filename(filename)
    
    # If the result is empty, generate a random name
    if not safe_name:
        safe_name = f'file_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    
    return safe_name


def format_date(date_obj, format_str='%B %d, %Y'):
    """
    Format a date object to a human-readable string.
    
    Args:
        date_obj: Date object to format
        format_str: strftime format string
    
    Returns:
        str: Formatted date string
    """
    if not date_obj:
        return ''
    
    if isinstance(date_obj, datetime):
        return date_obj.strftime(format_str)
    elif isinstance(date_obj, date):
        return date_obj.strftime(format_str)
    else:
        return str(date_obj)


def get_mime_type(filename):
    """
    Get the MIME type based on file extension.
    
    Args:
        filename: Name of the file
    
    Returns:
        str: MIME type string
    """
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    mime_types = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp'
    }
    
    return mime_types.get(ext, 'application/octet-stream')


def generate_unique_filename(original_filename):
    """
    Generate a unique filename with timestamp prefix.
    
    Args:
        original_filename: Original filename
    
    Returns:
        str: Unique filename
    """
    safe_name = sanitize_filename(original_filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
    name, ext = os.path.splitext(safe_name)
    return f'{timestamp}_{name}{ext}'


def validate_email(email):
    """
    Validate email format.
    
    Args:
        email: Email address to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    
    # Simple email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password):
    """
    Validate password strength.
    
    Args:
        password: Password to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, 'Password is required'
    
    if len(password) < 6:
        return False, 'Password must be at least 6 characters long'
    
    return True, ''