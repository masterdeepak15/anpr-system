"""Core components and interfaces"""

from .interfaces import (
    IStreamSource,
    IDetector,
    IOCREngine,
    IImageProcessor,
    IValidator
)
from .frame import Frame
from .result import DetectionResult, PlateResult
from .enums import ProcessingStatus, CameraStatus

__all__ = [
    'IStreamSource',
    'IDetector',
    'IOCREngine',
    'IImageProcessor',
    'IValidator',
    'Frame',
    'DetectionResult',
    'PlateResult',
    'ProcessingStatus',
    'CameraStatus'
]