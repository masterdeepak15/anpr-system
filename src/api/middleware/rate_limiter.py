"""Rate limiting middleware"""

from flask import request, jsonify
from functools import wraps
import time
from collections import defaultdict
import threading

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, key: str, max_requests: int, window: int) -> bool:
        """
        Check if request is allowed
        
        Args:
            key: Client identifier
            max_requests: Max requests allowed
            window: Time window in seconds
            
        Returns:
            bool: True if allowed
        """
        now = time.time()
        
        with self.lock:
            # Clean old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if now - req_time < window
            ]
            
            # Check limit
            if len(self.requests[key]) >= max_requests:
                return False
            
            # Add current request
            self.requests[key].append(now)
            return True


# Global rate limiter instance
limiter = RateLimiter()


def rate_limit(max_requests: int = 10, window: int = 60):
    """
    Rate limiting decorator
    
    Args:
        max_requests: Maximum requests allowed
        window: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Use IP address as key
            key = request.remote_addr
            
            if not limiter.is_allowed(key, max_requests, window):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window
                }), 429
            
            return f(*args, **kwargs)
        return decorated
    return decorator