"""Result data structures for detections and OCR"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import time

@dataclass
class DetectionResult:
    """
    Generic detection result
    
    Attributes:
        bbox: Bounding box as (x1, y1, x2, y2)
        confidence: Detection confidence score (0-1)
        class_id: Class identifier
        class_name: Human-readable class name
        features: Optional feature vector
    """
    bbox: tuple  # (x1, y1, x2, y2)
    confidence: float
    class_id: int
    class_name: str = ""
    features: Optional[List[float]] = None
    
    def __post_init__(self):
        """Validate detection result"""
        if len(self.bbox) != 4:
            raise ValueError("Bounding box must have 4 coordinates")
        
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
    
    @property
    def area(self) -> float:
        """Calculate bounding box area"""
        x1, y1, x2, y2 = self.bbox
        return (x2 - x1) * (y2 - y1)
    
    @property
    def center(self) -> tuple:
        """Get center point of bounding box"""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'bbox': self.bbox,
            'confidence': self.confidence,
            'class_id': self.class_id,
            'class_name': self.class_name,
            'area': self.area,
            'center': self.center
        }


@dataclass
class PlateResult:
    """
    License plate recognition result
    
    Attributes:
        plate_text: Recognized plate text
        confidence: Overall recognition confidence
        bbox: Plate bounding box
        frame_id: Source frame ID
        camera_id: Source camera ID
        timestamp: Detection timestamp
        character_confidences: Per-character confidence scores
        raw_detections: Raw detection results from multiple frames
        metadata: Additional metadata
    """
    plate_text: str
    confidence: float
    bbox: tuple
    frame_id: int
    camera_id: str
    timestamp: float
    character_confidences: List[float] = field(default_factory=list)
    raw_detections: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate plate result"""
        if not self.plate_text:
            raise ValueError("Plate text cannot be empty")
        
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        
        if self.timestamp <= 0:
            self.timestamp = time.time()
    
    @property
    def avg_char_confidence(self) -> float:
        """Calculate average character confidence"""
        if not self.character_confidences:
            return 0.0
        return sum(self.character_confidences) / len(self.character_confidences)
    
    @property
    def min_char_confidence(self) -> float:
        """Get minimum character confidence"""
        if not self.character_confidences:
            return 0.0
        return min(self.character_confidences)
    
    @property
    def consensus_count(self) -> int:
        """Count how many raw detections match the final result"""
        return sum(1 for det in self.raw_detections if det == self.plate_text)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'plate_text': self.plate_text,
            'confidence': self.confidence,
            'bbox': self.bbox,
            'frame_id': self.frame_id,
            'camera_id': self.camera_id,
            'timestamp': self.timestamp,
            'character_confidences': self.character_confidences,
            'raw_detections': self.raw_detections,
            'avg_char_confidence': self.avg_char_confidence,
            'min_char_confidence': self.min_char_confidence,
            'consensus_count': self.consensus_count,
            'metadata': self.metadata
        }
    
    def __repr__(self) -> str:
        return (f"PlateResult(plate_text='{self.plate_text}', "
                f"confidence={self.confidence:.2f}, "
                f"camera_id='{self.camera_id}', "
                f"frame_id={self.frame_id})")