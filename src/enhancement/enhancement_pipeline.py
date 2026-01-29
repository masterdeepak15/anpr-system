"""Enhancement pipeline with multiple strategies"""

import cv2
import numpy as np
from typing import List, Callable
import logging

class EnhancementPipeline:
    """
    Configurable image enhancement pipeline
    
    Allows chaining multiple enhancement operations
    """
    
    def __init__(self):
        """Initialize enhancement pipeline"""
        self.operations: List[Callable] = []
        self.logger = logging.getLogger("EnhancementPipeline")
    
    def add_operation(self, operation: Callable, name: str = None):
        """
        Add enhancement operation to pipeline
        
        Args:
            operation: Function that takes and returns np.ndarray
            name: Optional operation name for logging
        """
        if name:
            operation.__name__ = name
        self.operations.append(operation)
    
    def process(self, image: np.ndarray) -> np.ndarray:
        """
        Apply all operations in sequence
        
        Args:
            image: Input image
            
        Returns:
            np.ndarray: Processed image
        """
        result = image.copy()
        
        for operation in self.operations:
            try:
                result = operation(result)
                self.logger.debug(f"Applied: {operation.__name__}")
            except Exception as e:
                self.logger.error(f"Operation {operation.__name__} failed: {e}")
        
        return result
    
    def clear(self):
        """Remove all operations"""
        self.operations.clear()
    
    def __len__(self) -> int:
        return len(self.operations)


# Predefined enhancement strategies

def create_basic_enhancement() -> EnhancementPipeline:
    """Create basic enhancement pipeline"""
    pipeline = EnhancementPipeline()
    
    pipeline.add_operation(
        lambda img: cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img,
        "to_grayscale"
    )
    
    pipeline.add_operation(
        lambda img: cv2.GaussianBlur(img, (3, 3), 0),
        "gaussian_blur"
    )
    
    pipeline.add_operation(
        lambda img: cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        ),
        "adaptive_threshold"
    )
    
    return pipeline


def create_advanced_enhancement() -> EnhancementPipeline:
    """Create advanced enhancement pipeline"""
    pipeline = EnhancementPipeline()
    
    # Grayscale
    pipeline.add_operation(
        lambda img: cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img,
        "to_grayscale"
    )
    
    # Denoise
    pipeline.add_operation(
        lambda img: cv2.fastNlMeansDenoising(img, None, 10, 7, 21),
        "denoise"
    )
    
    # CLAHE
    def apply_clahe(img):
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(img)
    
    pipeline.add_operation(apply_clahe, "clahe")
    
    # Morphological closing
    pipeline.add_operation(
        lambda img: cv2.morphologyEx(
            img, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        ),
        "morphology_close"
    )
    
    # Binarize
    pipeline.add_operation(
        lambda img: cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        ),
        "adaptive_threshold"
    )
    
    return pipeline