"""Enumerations for the ANPR system"""

from enum import Enum, auto

class ProcessingStatus(Enum):
    """Frame processing status"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"
    TIMEOUT = "timeout"
    
    def __str__(self):
        return self.value


class CameraStatus(Enum):
    """Camera connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    DISABLED = "disabled"
    
    def __str__(self):
        return self.value


class ModelType(Enum):
    """ML model types"""
    VEHICLE_DETECTOR = "vehicle_detector"
    PLATE_DETECTOR = "plate_detector"
    CHAR_CLASSIFIER = "char_classifier"
    
    def __str__(self):
        return self.value


class DetectionClass(Enum):
    """Detection class IDs (COCO dataset)"""
    CAR = 2
    MOTORCYCLE = 3
    BUS = 5
    TRUCK = 7
    
    @classmethod
    def is_vehicle(cls, class_id: int) -> bool:
        """Check if class ID is a vehicle"""
        return class_id in [c.value for c in cls]


class ValidationLevel(Enum):
    """Validation strictness levels"""
    STRICT = "strict"      # All rules must pass
    NORMAL = "normal"      # Most rules must pass (70%+)
    LENIENT = "lenient"    # Basic rules only (50%+)
    
    def __str__(self):
        return self.value


class APIResponseStatus(Enum):
    """API response status codes"""
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    CONFLICT = 409
    SERVER_ERROR = 500
    
    def __int__(self):
        return self.value