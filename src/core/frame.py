"""Frame data structures"""

from dataclasses import dataclass, field
from typing import Dict, Any
import numpy as np
import time

@dataclass
class Frame:
    """
    Immutable frame data structure
    
    Attributes:
        camera_id: Unique camera identifier
        timestamp: Unix timestamp when frame was captured
        frame_id: Sequential frame number
        image: Frame data as numpy array
        metadata: Additional frame metadata
    """
    camera_id: str
    timestamp: float
    frame_id: int
    image: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate frame data after initialization"""
        if not isinstance(self.image, np.ndarray):
            raise TypeError("Frame image must be a numpy array")
        
        if self.image.size == 0:
            raise ValueError("Frame image cannot be empty")
        
        if self.timestamp <= 0:
            self.timestamp = time.time()
    
    @property
    def shape(self) -> tuple:
        """Get frame image shape"""
        return self.image.shape
    
    @property
    def height(self) -> int:
        """Get frame height"""
        return self.image.shape[0]
    
    @property
    def width(self) -> int:
        """Get frame width"""
        return self.image.shape[1]
    
    @property
    def channels(self) -> int:
        """Get number of color channels"""
        return self.image.shape[2] if len(self.image.shape) > 2 else 1
    
    def copy(self) -> 'Frame':
        """Create a deep copy of the frame"""
        return Frame(
            camera_id=self.camera_id,
            timestamp=self.timestamp,
            frame_id=self.frame_id,
            image=self.image.copy(),
            metadata=self.metadata.copy()
        )
    
    def __repr__(self) -> str:
        return (f"Frame(camera_id='{self.camera_id}', "
                f"frame_id={self.frame_id}, "
                f"shape={self.shape}, "
                f"timestamp={self.timestamp:.2f})")