"""License plate detection using classical CV and optional ML"""

import cv2
import numpy as np
import time
from typing import List, Tuple, Optional
import logging

try:
    import onnxruntime as ort
except ImportError:
    ort = None

from ..core.interfaces import IDetector
from ..core.result import DetectionResult

class PlateDetector(IDetector):
    """
    License plate detection using hybrid approach:
    1. Classical CV methods (edge detection, contours)
    2. Optional ML model for refinement
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        use_ml_model: bool = True,
        min_plate_width: int = 80,
        max_plate_width: int = 300,
        aspect_ratio_range: Tuple[float, float] = (2.0, 5.5),
        min_rectangularity: float = 0.6
    ):
        """
        Initialize plate detector
        
        Args:
            model_path: Path to plate detection model (optional)
            use_ml_model: Whether to use ML refinement
            min_plate_width: Minimum plate width in pixels
            max_plate_width: Maximum plate width in pixels
            aspect_ratio_range: (min, max) aspect ratio for plates
            min_rectangularity: Minimum rectangularity score
        """
        self.model_path = model_path
        self.use_ml_model = use_ml_model and model_path is not None
        self.min_plate_width = min_plate_width
        self.max_plate_width = max_plate_width
        self.aspect_ratio_range = aspect_ratio_range
        self.min_rectangularity = min_rectangularity
        
        self._ml_session: Optional[ort.InferenceSession] = None
        self._last_inference_time = 0.0
        
        self.logger = logging.getLogger("PlateDetector")
        
        # Load ML model if specified
        if self.use_ml_model:
            self.load_model(model_path)
    
    def load_model(self, model_path: str) -> bool:
        """Load plate detection ML model (optional)"""
        if not self.use_ml_model or ort is None:
            return False
        
        try:
            self.logger.info(f"Loading plate detection model: {model_path}")
            
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.intra_op_num_threads = 2
            
            self._ml_session = ort.InferenceSession(
                model_path,
                sess_options=sess_options,
                providers=['CPUExecutionProvider']
            )
            
            self.logger.info("Plate detection model loaded")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            self.use_ml_model = False
            return False
    
    def detect(self, vehicle_roi: np.ndarray) -> List[DetectionResult]:
        """
        Detect license plate within vehicle ROI
        
        Args:
            vehicle_roi: Cropped vehicle image
            
        Returns:
            List[DetectionResult]: Detected plates (usually 0 or 1)
        """
        start_time = time.time()
        
        try:
            # Stage 1: Classical CV detection (fast, high recall)
            candidates = self._detect_classical(vehicle_roi)
            
            # Stage 2: ML refinement (optional, for precision)
            if self.use_ml_model and self._ml_session:
                candidates = self._refine_with_ml(vehicle_roi, candidates)
            
            self._last_inference_time = (time.time() - start_time) * 1000
            
            self.logger.debug(
                f"Detected {len(candidates)} plate candidates in {self._last_inference_time:.2f}ms"
            )
            
            return candidates
            
        except Exception as e:
            self.logger.error(f"Plate detection failed: {e}")
            return []
    
    def _detect_classical(self, image: np.ndarray) -> List[DetectionResult]:
        """
        Classical CV-based plate detection
        
        Args:
            image: Vehicle ROI image
            
        Returns:
            List[DetectionResult]: Candidate plates
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply bilateral filter to reduce noise while keeping edges
        blurred = cv2.bilateralFilter(gray, 11, 17, 17)
        
        # Edge detection
        edged = cv2.Canny(blurred, 30, 200)
        
        # Morphological closing to connect broken edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(
            closed,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        candidates = []
        
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size
            if w < self.min_plate_width or w > self.max_plate_width:
                continue
            
            # Filter by aspect ratio (plates are wider than tall)
            aspect_ratio = w / float(h) if h > 0 else 0
            if not (self.aspect_ratio_range[0] <= aspect_ratio <= self.aspect_ratio_range[1]):
                continue
            
            # Calculate rectangularity (how rectangular the contour is)
            rect_area = w * h
            contour_area = cv2.contourArea(contour)
            rectangularity = contour_area / rect_area if rect_area > 0 else 0
            
            if rectangularity < self.min_rectangularity:
                continue
            
            # Calculate confidence based on rectangularity and aspect ratio
            # Perfect plate aspect ratio is around 3.0-4.0
            optimal_ratio = 3.5
            ratio_score = 1.0 - min(abs(aspect_ratio - optimal_ratio) / optimal_ratio, 1.0)
            confidence = (rectangularity + ratio_score) / 2.0
            
            candidates.append(DetectionResult(
                bbox=(x, y, x + w, y + h),
                confidence=confidence,
                class_id=0,  # plate class
                class_name="license_plate"
            ))
        
        # Sort by confidence and return top candidates
        candidates.sort(key=lambda d: d.confidence, reverse=True)
        return candidates[:3]  # Return top 3 candidates
    
    def _refine_with_ml(
        self,
        image: np.ndarray,
        candidates: List[DetectionResult]
    ) -> List[DetectionResult]:
        """
        Use ML model to refine candidate plates
        
        Args:
            image: Original vehicle ROI
            candidates: Candidate detections from classical method
            
        Returns:
            List[DetectionResult]: Refined detections
        """
        if not self._ml_session:
            return candidates
        
        refined = []
        
        for candidate in candidates:
            try:
                x1, y1, x2, y2 = map(int, candidate.bbox)
                
                # Extract candidate region
                roi = image[y1:y2, x1:x2]
                
                if roi.size == 0:
                    continue
                
                # Prepare for ML model
                input_tensor = self._prepare_ml_input(roi)
                
                # Run inference
                input_name = self._ml_session.get_inputs()[0].name
                output_name = self._ml_session.get_outputs()[0].name
                
                result = self._ml_session.run(
                    [output_name],
                    {input_name: input_tensor}
                )
                
                # Parse result (assuming binary classification: plate/non-plate)
                # Adjust based on your model's output format
                confidence = float(result[0][0][1]) if len(result[0][0]) > 1 else float(result[0][0][0])
                
                if confidence > 0.7:  # Threshold
                    refined.append(DetectionResult(
                        bbox=candidate.bbox,
                        confidence=confidence,
                        class_id=0,
                        class_name="license_plate"
                    ))
                    
            except Exception as e:
                self.logger.debug(f"ML refinement failed for candidate: {e}")
                continue
        
        return refined if refined else candidates
    
    def _prepare_ml_input(self, roi: np.ndarray) -> np.ndarray:
        """
        Prepare ROI for ML model input
        
        Args:
            roi: Plate candidate ROI
            
        Returns:
            np.ndarray: Model input tensor
        """
        # Resize to model input size (e.g., 128x64)
        resized = cv2.resize(roi, (128, 64))
        
        # Normalize
        normalized = resized.astype(np.float32) / 255.0
        
        # Convert to RGB if grayscale
        if len(normalized.shape) == 2:
            normalized = cv2.cvtColor(normalized, cv2.COLOR_GRAY2RGB)
        
        # HWC to NCHW
        transposed = np.transpose(normalized, (2, 0, 1))
        
        # Add batch dimension
        batched = np.expand_dims(transposed, axis=0)
        
        return batched
    
    def get_inference_time(self) -> float:
        """Get last inference time in milliseconds"""
        return self._last_inference_time
    
    def __repr__(self) -> str:
        return (f"PlateDetector(use_ml={self.use_ml_model}, "
                f"width_range=({self.min_plate_width}, {self.max_plate_width}))")