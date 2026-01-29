"""Authentication middleware"""

from functools import wraps
from flask import request, jsonify
import os

def require_api_key(f):
    """Decorator to require API key"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_key = os.getenv('API_KEY', 'your-api-key-here')
        
        if not api_key or api_key != expected_key:
            return jsonify({'error': 'Unauthorized'}), 401
        
        return f(*args, **kwargs)
    return decorated


def optional_api_key(f):
    """Decorator for optional API key (adds user context if valid)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_key = os.getenv('API_KEY')
        
        # Add authenticated flag to request
        request.authenticated = (api_key == expected_key) if expected_key else False
        
        return f(*args, **kwargs)
    return decorated