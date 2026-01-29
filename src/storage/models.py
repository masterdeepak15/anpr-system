"""Data models for database entities"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import time

@dataclass
class CameraModel:
    """Camera configuration model"""
    camera_id: str
    name: str
    rtsp_url: str
    location: Optional[str] = None
    frame_skip: int = 2
    enabled: bool = True
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CameraModel':
        """Create from dictionary"""
        return cls(**data)

@dataclass
class PlateResultModel:
    """Plate result model"""
    id: Optional[int] = None
    camera_id: str = ""
    plate_text: str = ""
    confidence: float = 0.0
    timestamp: float = 0.0
    frame_id: int = 0
    bbox: Optional[tuple] = None
    character_confidences: Optional[list] = None
    raw_detections: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class MetricModel:
    """Metric model"""
    id: Optional[int] = None
    metric_name: str = ""
    metric_value: float = 0.0
    camera_id: Optional[str] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)