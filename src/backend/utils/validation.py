"""
Validation Utilities

This module provides helper functions for input validation.
"""

from flask import jsonify


def validate_required_fields(data, required_fields):
    """Validate that all required fields are present in the data.
    
    Args:
        data: Dictionary containing the data to validate
        required_fields: List of required field names
        
    Returns:
        dict: Dictionary with 'valid' (bool) and 'error' (str) keys
    """
    if not all(field in data for field in required_fields):
        missing_fields = [field for field in required_fields if field not in data]
        return {
            'valid': False,
            'error': f"Missing required fields: {', '.join(missing_fields)}"
        }
    
    return {'valid': True}


def validate_email_format(email):
    """Validate email format.
    
    Args:
        email: Email to validate
        
    Returns:
        dict: Dictionary with 'valid' (bool) and 'error' (str) keys
    """
    import re
    
    # Handle None case
    if email is None:
        return {
            'valid': False,
            'error': "Invalid email format"
        }
    
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return {
            'valid': False,
            'error': "Invalid email format"
        }
    
    return {'valid': True}


def validate_password_strength(password):
    """Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        dict: Dictionary with 'valid' (bool) and 'error' (str) keys
    """
    # Handle None case
    if password is None:
        return {
            'valid': False,
            'error': "Password must be at least 8 characters"
        }
    
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    
    # Optional: Add more validations
    # Has uppercase
    # if not any(c.isupper() for c in password):
    #     errors.append("Password must include at least one uppercase letter")
    
    # Has number
    # if not any(c.isdigit() for c in password):
    #     errors.append("Password must include at least one number")
    
    if errors:
        return {
            'valid': False,
            'error': ' '.join(errors)
        }
    
    return {'valid': True}


def api_error(message, status_code=400):
    """Create a standardized API error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        
    Returns:
        tuple: (response, status_code)
    """
    return jsonify({"error": message}), status_code 