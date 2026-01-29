"""License plate image enhancement for better OCR"""

import cv2
import numpy as np
from typing import Optional, Tuple
import logging

from ..core.interfaces import IImageProcessor

class PlateEnhancer(IImageProcessor):
    """
    Enhance license plate image quality for OCR
    
    Techniques:
    - Perspective correction (deskewing)
    - Contrast enhancement
    - Noise reduction
    - Binarization
    """
    
    def __init__(
        self,
        target_size: Tuple[int, int] = (280, 70),
        denoise_strength: int = 10,
        clahe_clip_limit: float = 2.0
    ):
        """
        Initialize plate enhancer
        
        Args:
            target_size: (width, height) for standardized plate size
            denoise_strength: Denoising filter strength
            clahe_clip_limit: CLAHE clip limit for contrast
        """
        self.target_size = target_size
        self.denoise_strength = denoise_strength
        self.clahe_clip_limit = clahe_clip_limit
        
        self.logger = logging.getLogger("PlateEnhancer")
    
    def process(self, plate_image: np.ndarray) -> np.ndarray:
        """
        Apply full enhancement pipeline
        
        Args:
            plate_image: Raw plate image
            
        Returns:
            np.ndarray: Enhanced plate image
        """
        if plate_image is None or plate_image.size == 0:
            raise ValueError("Invalid plate image")
        
        try:
            # 1. Deskew (perspective correction)
            deskewed = self._deskew(plate_image)
            
            # 2. Resize to standard size
            resized = cv2.resize(deskewed, self.target_size)
            
            # 3. Convert to grayscale
            if len(resized.shape) == 3:
                gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            else:
                gray = resized
            
            # 4. Denoise
            denoised = cv2.fastNlMeansDenoising(
                gray,
                None,
                self.denoise_strength,
                7,
                21
            )
            
            # 5. Enhance contrast
            enhanced = self._enhance_contrast(denoised)
            
            # 6. Binarize
            binary = self._binarize(enhanced)
            
            return binary
            
        except Exception as e:
            self.logger.error(f"Enhancement failed: {e}")
            # Return grayscale version as fallback
            if len(plate_image.shape) == 3:
                return cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
            return plate_image
    
    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Correct perspective distortion
        
        Args:
            image: Input image
            
        Returns:
            np.ndarray: Deskewed image
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Find edges
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
            
            if lines is None or len(lines) == 0:
                return image
            
            # Calculate median angle
            angles = []
            for rho, theta in lines[:, 0]:
                angle = np.degrees(theta) - 90
                angles.append(angle)
            
            median_angle = np.median(angles)
            
            # Only rotate if significant skew
            if abs(median_angle) > 0.5:
                h, w = image.shape[:2]
                center = (w // 2, h // 2)
                
                # Rotation matrix
                matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                
                # Apply rotation
                rotated = cv2.warpAffine(
                    image,
                    matrix,
                    (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                
                return rotated
            
            return image
            
        except Exception as e:
            self.logger.debug(f"Deskew failed: {e}")
            return image
    
    def _enhance_contrast(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Adaptive histogram equalization
        
        Args:
            gray_image: Grayscale input
            
        Returns:
            np.ndarray: Contrast enhanced image
        """
        clahe = cv2.createCLAHE(
            clipLimit=self.clahe_clip_limit,
            tileGridSize=(8, 8)
        )
        enhanced = clahe.apply(gray_image)
        return enhanced
    
    def _binarize(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Adaptive thresholding for binarization
        
        Args:
            gray_image: Grayscale input
            
        Returns:
            np.ndarray: Binary image
        """
        binary = cv2.adaptiveThreshold(
            gray_image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # Block size
            2    # C constant
        )
        return binary
    
    def apply_morphology(
        self,
        binary_image: np.ndarray,
        operation: str = "close",
        kernel_size: Tuple[int, int] = (3, 3)
    ) -> np.ndarray:
        """
        Apply morphological operations
        
        Args:
            binary_image: Binary input image
            operation: "erode", "dilate", "open", or "close"
            kernel_size: Morphological kernel size
            
        Returns:
            np.ndarray: Processed image
        """
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        
        if operation == "erode":
            return cv2.erode(binary_image, kernel)
        elif operation == "dilate":
            return cv2.dilate(binary_image, kernel)
        elif operation == "open":
            return cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)
        elif operation == "close":
            return cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
        
        return binary_image
    
    def remove_border(self, image: np.ndarray, border_size: int = 2) -> np.ndarray:
        """
        Remove border artifacts
        
        Args:
            image: Input image
            border_size: Border size in pixels
            
        Returns:
            np.ndarray: Image with border removed
        """
        h, w = image.shape[:2]
        return image[border_size:h-border_size, border_size:w-border_size]
    
    def __repr__(self) -> str:
        return f"PlateEnhancer(target_size={self.target_size})"