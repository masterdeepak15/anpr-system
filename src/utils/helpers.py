"""General helper functions"""

import time
from datetime import datetime
from typing import Any, Dict
import hashlib
import json

def get_timestamp() -> float:
    """Get current Unix timestamp"""
    return time.time()


def format_timestamp(timestamp: float, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format Unix timestamp to string
    
    Args:
        timestamp: Unix timestamp
        format_str: Format string
        
    Returns:
        str: Formatted timestamp
    """
    return datetime.fromtimestamp(timestamp).strftime(format_str)


def generate_id(data: str) -> str:
    """
    Generate unique ID from string
    
    Args:
        data: Input string
        
    Returns:
        str: MD5 hash
    """
    return hashlib.md5(data.encode()).hexdigest()


def dict_to_json_str(data: Dict[str, Any]) -> str:
    """Convert dictionary to JSON string"""
    return json.dumps(data, default=str)


def json_str_to_dict(json_str: str) -> Dict[str, Any]:
    """Convert JSON string to dictionary"""
    return json.loads(json_str)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value between min and max
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        float: Clamped value
    """
    return max(min_val, min(value, max_val))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safe division with default value
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
        
    Returns:
        float: Result or default
    """
    return numerator / denominator if denominator != 0 else default