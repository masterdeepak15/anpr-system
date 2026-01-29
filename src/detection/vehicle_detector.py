"""Vehicle detection using ONNX Runtime"""

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

class VehicleDetector(IDetector):
    """
    Vehicle detection using ONNX model (CPU-optimized)
    
    Supports YOLO, SSD, or similar object detection models
    """
    
    def __init__(
        self,
        model_path: str,
        input_size: Tuple[int, int] = (640, 640),
        confidence_threshold: float = 0.5,
        nms_threshold: float = 0.4,
        vehicle_classes: List[int] = None
    ):
        """
        Initialize vehicle detector
        
        Args:
            model_path: Path to ONNX model
            input_size: Model input size (width, height)
            confidence_threshold: Minimum confidence for detection
            nms_threshold: NMS IoU threshold
            vehicle_classes: List of vehicle class IDs (COCO: car=2, motorcycle=3, bus=5, truck=7)
        """
        self.model_path = model_path
        self.input_size = input_size
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.vehicle_classes = vehicle_classes or [2, 3, 5, 7]  # COCO vehicle classes
        
        self._session: Optional[ort.InferenceSession] = None
        self._input_name: Optional[str] = None
        self._output_names: Optional[List[str]] = None
        self._last_inference_time = 0.0
        
        self.logger = logging.getLogger("VehicleDetector")
        
        # Load model
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str) -> bool:
        """Load ONNX model with CPU-optimized session"""
        if ort is None:
            self.logger.error("ONNX Runtime not installed. Install with: pip install onnxruntime")
            return False
        
        try:
            self.logger.info(f"Loading vehicle detection model: {model_path}")
            
            # CPU-optimized session options
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.intra_op_num_threads = 4  # Tune based on CPU
            sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            
            # Create session with CPU provider
            self._session = ort.InferenceSession(
                model_path,
                sess_options=sess_options,
                providers=['CPUExecutionProvider']
            )
            
            # Get input/output names
            self._input_name = self._session.get_inputs()[0].name
            self._output_names = [output.name for output in self._session.get_outputs()]
            
            # Log model info
            input_shape = self._session.get_inputs()[0].shape
            self.logger.info(f"Model loaded successfully")
            self.logger.info(f"Input shape: {input_shape}")
            self.logger.info(f"Output names: {self._output_names}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False
    
    def detect(self, image: np.ndarray) -> List[DetectionResult]:
        """
        Run vehicle detection
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            List[DetectionResult]: Detected vehicles
        """
        if self._session is None:
            self.logger.warning("Model not loaded")
            return []
        
        start_time = time.time()
        
        try:
            # Preprocess
            input_tensor = self._preprocess(image)
            
            # Inference
            outputs = self._session.run(
                self._output_names,
                {self._input_name: input_tensor}
            )
            
            # Postprocess
            detections = self._postprocess(outputs, image.shape)
            
            # Record inference time
            self._last_inference_time = (time.time() - start_time) * 1000
            
            self.logger.debug(
                f"Detected {len(detections)} vehicles in {self._last_inference_time:.2f}ms"
            )
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Detection failed: {e}")
            return []
    
    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Prepare image for model input
        
        Args:
            image: Input image (BGR)
            
        Returns:
            np.ndarray: Preprocessed tensor
        """
        # Resize to model input size
        resized = cv2.resize(image, self.input_size)
        
        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1]
        normalized = rgb.astype(np.float32) / 255.0
        
        # HWC to NCHW format
        transposed = np.transpose(normalized, (2, 0, 1))
        
        # Add batch dimension
        batched = np.expand_dims(transposed, axis=0)
        
        return batched
    
    def _postprocess(
        self,
        outputs: List[np.ndarray],
        original_shape: Tuple[int, ...]
    ) -> List[DetectionResult]:
        """
        Parse model outputs and filter for vehicles
        
        Args:
            outputs: Model output tensors
            original_shape: Original image shape
            
        Returns:
            List[DetectionResult]: Filtered and processed detections
        """
        detections = []
        
        # Parse output (format depends on model architecture)
        # This is a generic implementation for YOLO-style outputs
        predictions = outputs[0][0]  # Remove batch dimension
        
        orig_h, orig_w = original_shape[:2]
        scale_x = orig_w / self.input_size[0]
        scale_y = orig_h / self.input_size[1]
        
        for pred in predictions:
            # Skip if confidence too low
            if len(pred) < 5:
                continue
            
            confidence = pred[4]
            
            if confidence < self.confidence_threshold:
                continue
            
            # Get class scores (if available)
            if len(pred) > 5:
                class_scores = pred[5:]
                class_id = np.argmax(class_scores)
                class_confidence = class_scores[class_id]
            else:
                class_id = 0
                class_confidence = confidence
            
            # Filter by vehicle classes
            if class_id not in self.vehicle_classes:
                continue
            
            # Convert from center format to corner format
            x_center, y_center, width, height = pred[0:4]
            x1 = (x_center - width / 2) * scale_x
            y1 = (y_center - height / 2) * scale_y
            x2 = (x_center + width / 2) * scale_x
            y2 = (y_center + height / 2) * scale_y
            
            # Ensure coordinates are within bounds
            x1 = max(0, min(x1, orig_w))
            y1 = max(0, min(y1, orig_h))
            x2 = max(0, min(x2, orig_w))
            y2 = max(0, min(y2, orig_h))
            
            detections.append(DetectionResult(
                bbox=(x1, y1, x2, y2),
                confidence=float(confidence * class_confidence),
                class_id=int(class_id),
                class_name=self._get_class_name(class_id)
            ))
        
        # Apply Non-Maximum Suppression
        detections = self._apply_nms(detections)
        
        return detections
    
    def _apply_nms(self, detections: List[DetectionResult]) -> List[DetectionResult]:
        """
        Apply Non-Maximum Suppression
        
        Args:
            detections: List of detections
            
        Returns:
            List[DetectionResult]: Filtered detections
        """
        if len(detections) == 0:
            return []
        
        boxes = np.array([d.bbox for d in detections])
        scores = np.array([d.confidence for d in detections])
        
        # OpenCV NMS
        indices = cv2.dnn.NMSBoxes(
            boxes.tolist(),
            scores.tolist(),
            self.confidence_threshold,
            self.nms_threshold
        )
        
        if len(indices) > 0:
            indices = indices.flatten()
            return [detections[i] for i in indices]
        
        return []
    
    def _get_class_name(self, class_id: int) -> str:
        """Get human-readable class name"""
        class_names = {
            2: "car",
            3: "motorcycle",
            5: "bus",
            7: "truck"
        }
        return class_names.get(class_id, f"vehicle_{class_id}")
    
    def get_inference_time(self) -> float:
        """Get last inference time in milliseconds"""
        return self._last_inference_time
    
    def __repr__(self) -> str:
        return (f"VehicleDetector(model_loaded={self._session is not None}, "
                f"confidence={self.confidence_threshold})")