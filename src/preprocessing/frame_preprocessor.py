"""Frame preprocessing for optimal detection performance"""

import cv2
import numpy as np
from typing import Optional, Tuple
import logging

from ..core.interfaces import IImageProcessor

class FramePreprocessor(IImageProcessor):
    """
    CPU-optimized frame preprocessing
    
    Features:
    - Efficient resizing
    - Normalization
    - ROI extraction
    - Caching for repeated operations
    """
    
    def __init__(
        self,
        target_width: int = 640,
        target_height: int = 480,
        normalize: bool = True,
        maintain_aspect_ratio: bool = False
    ):
        """
        Initialize preprocessor
        
        Args:
            target_width: Target frame width
            target_height: Target frame height
            normalize: Whether to normalize to [0, 1]
            maintain_aspect_ratio: Preserve aspect ratio during resize
        """
        self.target_width = target_width
        self.target_height = target_height
        self.normalize = normalize
        self.maintain_aspect_ratio = maintain_aspect_ratio
        
        self.logger = logging.getLogger("FramePreprocessor")
        
        # Cache for repeated operations
        self._last_input_shape = None
        self._cached_resize_params = None
    
    def process(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for detection
        
        Args:
            image: Input frame
            
        Returns:
            np.ndarray: Preprocessed frame
        """
        if image is None or image.size == 0:
            raise ValueError("Invalid input image")
        
        # Resize
        processed = self._resize(image)
        
        # Normalize if requested
        if self.normalize:
            processed = self._normalize(processed)
        
        return processed
    
    def _resize(self, image: np.ndarray) -> np.ndarray:
        """
        Resize image with optional aspect ratio preservation
        
        Args:
            image: Input image
            
        Returns:
            np.ndarray: Resized image
        """
        h, w = image.shape[:2]
        
        # Check if already correct size
        if h == self.target_height and w == self.target_width:
            return image
        
        if self.maintain_aspect_ratio:
            # Calculate scaling to fit within target dimensions
            scale = min(self.target_width / w, self.target_height / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # Resize
            resized = cv2.resize(
                image,
                (new_w, new_h),
                interpolation=cv2.INTER_AREA  # Best for downscaling
            )
            
            # Pad to target size
            top = (self.target_height - new_h) // 2
            bottom = self.target_height - new_h - top
            left = (self.target_width - new_w) // 2
            right = self.target_width - new_w - left
            
            padded = cv2.copyMakeBorder(
                resized,
                top, bottom, left, right,
                cv2.BORDER_CONSTANT,
                value=[0, 0, 0]
            )
            
            return padded
        else:
            # Direct resize (may distort aspect ratio)
            return cv2.resize(
                image,
                (self.target_width, self.target_height),
                interpolation=cv2.INTER_AREA
            )
    
    def _normalize(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize image to [0, 1] range
        
        Args:
            image: Input image
            
        Returns:
            np.ndarray: Normalized image
        """
        if image.dtype != np.float32:
            image = image.astype(np.float32)
        
        return image / 255.0
    
    def extract_roi(
        self,
        image: np.ndarray,
        bbox: Tuple[int, int, int, int],
        padding: int = 0
    ) -> np.ndarray:
        """
        Extract region of interest with optional padding
        
        Args:
            image: Input image
            bbox: Bounding box as (x1, y1, x2, y2)
            padding: Pixels to add around ROI
            
        Returns:
            np.ndarray: Extracted ROI
        """
        h, w = image.shape[:2]
        x1, y1, x2, y2 = bbox
        
        # Apply padding
        x1 = max(0, int(x1 - padding))
        y1 = max(0, int(y1 - padding))
        x2 = min(w, int(x2 + padding))
        y2 = min(h, int(y2 + padding))
        
        # Extract ROI
        roi = image[y1:y2, x1:x2]
        
        if roi.size == 0:
            self.logger.warning(f"Empty ROI extracted from bbox: {bbox}")
            return np.zeros((1, 1, 3), dtype=image.dtype)
        
        return roi
    
    def denormalize(self, image: np.ndarray) -> np.ndarray:
        """
        Convert normalized image back to [0, 255]
        
        Args:
            image: Normalized image
            
        Returns:
            np.ndarray: Denormalized image
        """
        if image.dtype == np.float32 or image.dtype == np.float64:
            return (image * 255).astype(np.uint8)
        return image
    
    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        Convert image to grayscale
        
        Args:
            image: Input image
            
        Returns:
            np.ndarray: Grayscale image
        """
        if len(image.shape) == 2:
            return image
        
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    def adjust_brightness_contrast(
        self,
        image: np.ndarray,
        alpha: float = 1.0,
        beta: int = 0
    ) -> np.ndarray:
        """
        Adjust brightness and contrast
        
        Args:
            image: Input image
            alpha: Contrast control (1.0-3.0)
            beta: Brightness control (0-100)
            
        Returns:
            np.ndarray: Adjusted image
        """
        return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    
    def __repr__(self) -> str:
        return (f"FramePreprocessor(target_size=({self.target_width}, {self.target_height}), "
                f"normalize={self.normalize})")