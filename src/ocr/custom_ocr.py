"""Custom OCR engine implementation"""

import numpy as np
from typing import Dict, Any, Optional
import logging

from ..core.interfaces import IOCREngine
from ..core.result import PlateResult
from .character_segmentation import CharacterSegmenter
from .character_classifier import CharacterClassifier
from .text_postprocessor import TextPostProcessor

class CustomOCREngine(IOCREngine):
    """
    Custom OCR implementation:
    1. Character segmentation (contour-based)
    2. Feature extraction
    3. Classification (using pre-trained model)
    4. Post-processing & validation
    """
    
    def __init__(
        self,
        classifier_model_path: str,
        country_code: str = "IN"
    ):
        """
        Initialize OCR engine
        
        Args:
            classifier_model_path: Path to character classifier model
            country_code: Country code for format rules
        """
        self.classifier_model_path = classifier_model_path
        self.country_code = country_code
        
        # Initialize components
        self.segmenter = CharacterSegmenter()
        self.classifier = CharacterClassifier(classifier_model_path)
        self.postprocessor = TextPostProcessor(country_code)
        
        self.logger = logging.getLogger("CustomOCR")
    
    def recognize(self, plate_image: np.ndarray) -> PlateResult:
        """
        Full OCR pipeline
        
        Args:
            plate_image: Enhanced plate image
            
        Returns:
            PlateResult: Recognition result
        """
        try:
            # 1. Segment characters
            char_segments = self.segmenter.segment(plate_image)
            
            if len(char_segments) == 0:
                self.logger.warning("No characters segmented")
                return self._create_empty_result()
            
            # 2. Classify each character
            recognized_chars = []
            char_confidences = []
            
            for segment in char_segments:
                char, confidence = self.classifier.classify(segment)
                recognized_chars.append(char)
                char_confidences.append(confidence)
            
            # 3. Post-process (combine characters)
            plate_text = "".join(recognized_chars)
            
            # 4. Apply format rules and corrections
            plate_text, was_corrected = self.postprocessor.process(plate_text)
            
            # 5. Calculate overall confidence
            overall_confidence = float(np.mean(char_confidences)) if char_confidences else 0.0
            
            # 6. Create result
            result = PlateResult(
                plate_text=plate_text,
                confidence=overall_confidence,
                bbox=(0, 0, plate_image.shape[1], plate_image.shape[0]),
                frame_id=0,
                camera_id="",
                timestamp=0.0,
                character_confidences=char_confidences,
                raw_detections=[plate_text]
            )
            
            self.logger.debug(
                f"OCR result: '{plate_text}' (confidence: {overall_confidence:.2f})"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"OCR failed: {e}")
            return self._create_empty_result()
    
    def set_country_format(self, country_code: str) -> None:
        """
        Update country format rules
        
        Args:
            country_code: Country code (e.g., 'IN', 'US')
        """
        self.country_code = country_code
        self.postprocessor.set_country(country_code)
        self.logger.info(f"Country format updated to: {country_code}")
    
    def _create_empty_result(self) -> PlateResult:
        """Create empty result for failures"""
        return PlateResult(
            plate_text="",
            confidence=0.0,
            bbox=(0, 0, 0, 0),
            frame_id=0,
            camera_id="",
            timestamp=0.0,
            character_confidences=[],
            raw_detections=[]
        )
    
    def __repr__(self) -> str:
        return f"CustomOCREngine(country={self.country_code})"