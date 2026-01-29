"""Abstract base classes and interfaces for the ANPR system"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import numpy as np

class IStreamSource(ABC):
    """Abstract interface for stream sources (RTSP, USB, File, etc.)"""
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to stream source
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read a single frame from the stream
        
        Returns:
            Optional[np.ndarray]: Frame as numpy array, None on error
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if stream is currently active
        
        Returns:
            bool: True if connected, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Clean up resources and close connection"""
        pass
    
    @abstractmethod
    def get_fps(self) -> float:
        """
        Get current stream FPS
        
        Returns:
            float: Frames per second
        """
        pass


class IDetector(ABC):
    """Generic detector interface for vehicle and plate detection"""
    
    @abstractmethod
    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run detection on image
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List[Dict]: List of detection results
        """
        pass
    
    @abstractmethod
    def load_model(self, model_path: str) -> bool:
        """
        Load detection model
        
        Args:
            model_path: Path to model file
            
        Returns:
            bool: True if loaded successfully
        """
        pass
    
    @abstractmethod
    def get_inference_time(self) -> float:
        """
        Get last inference time
        
        Returns:
            float: Inference time in milliseconds
        """
        pass


class IOCREngine(ABC):
    """Abstract OCR engine interface"""
    
    @abstractmethod
    def recognize(self, plate_image: np.ndarray) -> Dict[str, Any]:
        """
        Recognize text from plate image
        
        Args:
            plate_image: License plate image
            
        Returns:
            Dict: Recognition result with text and confidence
        """
        pass
    
    @abstractmethod
    def set_country_format(self, country_code: str) -> None:
        """
        Set expected plate format rules
        
        Args:
            country_code: Country code (e.g., 'IN', 'US')
        """
        pass


class IImageProcessor(ABC):
    """Abstract image processing interface"""
    
    @abstractmethod
    def process(self, image: np.ndarray) -> np.ndarray:
        """
        Process and return enhanced image
        
        Args:
            image: Input image
            
        Returns:
            np.ndarray: Processed image
        """
        pass


class IValidator(ABC):
    """Abstract validation interface"""
    
    @abstractmethod
    def validate(self, plate_text: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Validate plate text against rules
        
        Args:
            plate_text: Plate text to validate
            metadata: Additional metadata
            
        Returns:
            bool: True if valid
        """
        pass
    
    @abstractmethod
    def get_validation_score(self, plate_text: str) -> float:
        """
        Get validation confidence score
        
        Args:
            plate_text: Plate text to score
            
        Returns:
            float: Score between 0 and 1
        """
        pass