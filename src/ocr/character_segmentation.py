"""Character segmentation from plate image"""

import cv2
import numpy as np
from typing import List, Tuple
import logging

class CharacterSegmenter:
    """
    Segment individual characters from plate image
    
    Uses contour detection and filtering
    """
    
    def __init__(
        self,
        min_char_width: int = 10,
        max_char_width: int = 60,
        min_char_height: int = 20,
        max_char_height: int = 65,
        min_aspect_ratio: float = 0.2,
        max_aspect_ratio: float = 1.0
    ):
        """
        Initialize segmenter
        
        Args:
            min_char_width: Minimum character width
            max_char_width: Maximum character width
            min_char_height: Minimum character height
            max_char_height: Maximum character height
            min_aspect_ratio: Minimum height/width ratio
            max_aspect_ratio: Maximum height/width ratio
        """
        self.min_char_width = min_char_width
        self.max_char_width = max_char_width
        self.min_char_height = min_char_height
        self.max_char_height = max_char_height
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
        
        self.logger = logging.getLogger("CharacterSegmenter")
    
    def segment(self, plate_image: np.ndarray) -> List[np.ndarray]:
        """
        Segment characters from plate image
        
        Args:
            plate_image: Binary plate image
            
        Returns:
            List[np.ndarray]: List of character images
        """
        if plate_image is None or plate_image.size == 0:
            return []
        
        # Ensure binary image
        if len(plate_image.shape) == 3:
            gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_image.copy()
        
        # Find contours
        contours, _ = cv2.findContours(
            gray,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter and sort contours
        char_contours = self._filter_contours(contours)
        
        if len(char_contours) == 0:
            self.logger.warning("No valid character contours found")
            return []
        
        # Sort left to right
        char_contours.sort(key=lambda c: c[0])
        
        # Extract character regions
        char_segments = []
        
        for x, y, w, h in char_contours:
            # Add padding
            pad = 2
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(gray.shape[1], x + w + pad)
            y2 = min(gray.shape[0], y + h + pad)
            
            # Extract character
            char_img = gray[y1:y2, x1:x2]
            
            if char_img.size > 0:
                char_segments.append(char_img)
        
        self.logger.debug(f"Segmented {len(char_segments)} characters")
        
        return char_segments
    
    def _filter_contours(self, contours: List) -> List[Tuple[int, int, int, int]]:
        """
        Filter contours to find character candidates
        
        Args:
            contours: List of contours from cv2.findContours
            
        Returns:
            List of (x, y, w, h) tuples
        """
        char_contours = []
        
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size
            if w < self.min_char_width or w > self.max_char_width:
                continue
            
            if h < self.min_char_height or h > self.max_char_height:
                continue
            
            # Filter by aspect ratio
            aspect_ratio = h / float(w) if w > 0 else 0
            
            if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
                continue
            
            char_contours.append((x, y, w, h))
        
        return char_contours
    
    def merge_split_characters(
        self,
        segments: List[np.ndarray],
        max_gap: int = 5
    ) -> List[np.ndarray]:
        """
        Merge characters that were incorrectly split
        
        Args:
            segments: List of character segments
            max_gap: Maximum gap to consider for merging
            
        Returns:
            List of merged segments
        """
        # TODO: Implement character merging logic
        # This would detect when characters like "M" or "W" are split
        return segments