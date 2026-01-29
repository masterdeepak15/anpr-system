"""Incident detection (helmet, seatbelt, wrong-way, etc.)"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

try:
    import onnxruntime as ort
except ImportError:
    ort = None

@dataclass
class Incident:
    """Detected incident"""
    incident_type: str  # 'no_helmet', 'no_seatbelt', 'wrong_way', 'triple_riding'
    track_id: int
    confidence: float
    timestamp: float
    frame_id: int
    camera_id: str
    bbox: Tuple[int, int, int, int]
    metadata: Dict
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'incident_type': self.incident_type,
            'track_id': self.track_id,
            'confidence': self.confidence,
            'timestamp': self.timestamp,
            'frame_id': self.frame_id,
            'camera_id': self.camera_id,
            'bbox': self.bbox,
            'metadata': self.metadata
        }


class IncidentDetector:
    """
    Detect traffic violations and incidents
    
    Detects:
    - No helmet (motorcycles)
    - No seatbelt (cars)
    - Wrong-way driving
    - Triple riding (motorcycles)
    """
    
    def __init__(
        self,
        helmet_model_path: Optional[str] = None,
        seatbelt_model_path: Optional[str] = None,
        enable_helmet_detection: bool = True,
        enable_seatbelt_detection: bool = True,
        enable_wrong_way_detection: bool = True,
        enable_triple_riding_detection: bool = True
    ):
        """
        Initialize incident detector
        
        Args:
            helmet_model_path: Path to helmet detection model
            seatbelt_model_path: Path to seatbelt detection model
            enable_*: Enable/disable specific detections
        """
        self.enable_helmet = enable_helmet_detection
        self.enable_seatbelt = enable_seatbelt_detection
        self.enable_wrong_way = enable_wrong_way_detection
        self.enable_triple_riding = enable_triple_riding_detection
        
        self.helmet_detector = None
        self.seatbelt_detector = None
        
        # Load models if provided
        if helmet_model_path and self.enable_helmet:
            self._load_helmet_detector(helmet_model_path)
        
        if seatbelt_model_path and self.enable_seatbelt:
            self._load_seatbelt_detector(seatbelt_model_path)
        
        self.logger = logging.getLogger("IncidentDetector")
    
    def _load_helmet_detector(self, model_path: str) -> bool:
        """Load helmet detection model"""
        if ort is None:
            self.logger.warning("ONNX Runtime not available")
            return False
        
        try:
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            self.helmet_detector = ort.InferenceSession(
                model_path,
                sess_options=sess_options,
                providers=['CPUExecutionProvider']
            )
            
            self.logger.info("Helmet detector loaded")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load helmet detector: {e}")
            return False
    
    def _load_seatbelt_detector(self, model_path: str) -> bool:
        """Load seatbelt detection model"""
        if ort is None:
            self.logger.warning("ONNX Runtime not available")
            return False
        
        try:
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            self.seatbelt_detector = ort.InferenceSession(
                model_path,
                sess_options=sess_options,
                providers=['CPUExecutionProvider']
            )
            
            self.logger.info("Seatbelt detector loaded")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load seatbelt detector: {e}")
            return False
    
    def detect_incidents(
        self,
        frame: np.ndarray,
        tracked_vehicles: Dict,
        camera_id: str,
        frame_id: int,
        timestamp: float,
        flow_direction: Optional[Tuple[float, float]] = None
    ) -> List[Incident]:
        """
        Detect all incidents in frame
        
        Args:
            frame: Input frame
            tracked_vehicles: Dictionary of tracked vehicles
            camera_id: Camera identifier
            frame_id: Frame number
            timestamp: Frame timestamp
            flow_direction: Expected traffic flow direction (vx, vy)
            
        Returns:
            List of detected incidents
        """
        incidents = []
        
        for track_id, vehicle in tracked_vehicles.items():
            # Check vehicle class
            is_motorcycle = vehicle.class_name in ['motorcycle', 'bike', 'motorbike']
            is_car = vehicle.class_name in ['car', 'sedan', 'suv']
            
            # Extract vehicle ROI
            x1, y1, x2, y2 = vehicle.bbox
            vehicle_roi = frame[y1:y2, x1:x2]
            
            if vehicle_roi.size == 0:
                continue
            
            # No helmet detection (motorcycles)
            if self.enable_helmet and is_motorcycle:
                helmet_incident = self._detect_no_helmet(
                    vehicle_roi, vehicle, camera_id, frame_id, timestamp
                )
                if helmet_incident:
                    incidents.append(helmet_incident)
            
            # No seatbelt detection (cars)
            if self.enable_seatbelt and is_car:
                seatbelt_incident = self._detect_no_seatbelt(
                    vehicle_roi, vehicle, camera_id, frame_id, timestamp
                )
                if seatbelt_incident:
                    incidents.append(seatbelt_incident)
            
            # Wrong-way detection
            if self.enable_wrong_way and flow_direction:
                wrong_way_incident = self._detect_wrong_way(
                    vehicle, flow_direction, camera_id, frame_id, timestamp
                )
                if wrong_way_incident:
                    incidents.append(wrong_way_incident)
            
            # Triple riding detection (motorcycles)
            if self.enable_triple_riding and is_motorcycle:
                triple_riding_incident = self._detect_triple_riding(
                    vehicle_roi, vehicle, camera_id, frame_id, timestamp
                )
                if triple_riding_incident:
                    incidents.append(triple_riding_incident)
        
        return incidents
    
    def _detect_no_helmet(
        self,
        vehicle_roi: np.ndarray,
        vehicle,
        camera_id: str,
        frame_id: int,
        timestamp: float
    ) -> Optional[Incident]:
        """Detect no helmet on motorcycle"""
        
        if self.helmet_detector is None:
            # Fallback: simple heuristic (placeholder)
            # In production, use trained model
            return None
        
        try:
            # Preprocess ROI for helmet detection
            input_tensor = self._preprocess_for_detection(vehicle_roi, (224, 224))
            
            # Run inference
            input_name = self.helmet_detector.get_inputs()[0].name
            output_name = self.helmet_detector.get_outputs()[0].name
            
            result = self.helmet_detector.run(
                [output_name],
                {input_name: input_tensor}
            )[0]
            
            # Parse result (assuming binary classification: helmet/no_helmet)
            no_helmet_confidence = float(result[0][0])  # Adjust based on model output
            
            if no_helmet_confidence > 0.7:  # Threshold
                return Incident(
                    incident_type='no_helmet',
                    track_id=vehicle.track_id,
                    confidence=no_helmet_confidence,
                    timestamp=timestamp,
                    frame_id=frame_id,
                    camera_id=camera_id,
                    bbox=vehicle.bbox,
                    metadata={
                        'vehicle_class': vehicle.class_name,
                        'plate': vehicle.plate_text
                    }
                )
        
        except Exception as e:
            self.logger.error(f"Helmet detection error: {e}")
        
        return None
    
    def _detect_no_seatbelt(
        self,
        vehicle_roi: np.ndarray,
        vehicle,
        camera_id: str,
        frame_id: int,
        timestamp: float
    ) -> Optional[Incident]:
        """Detect no seatbelt in car"""
        
        if self.seatbelt_detector is None:
            return None
        
        try:
            # Preprocess ROI
            input_tensor = self._preprocess_for_detection(vehicle_roi, (224, 224))
            
            # Run inference
            input_name = self.seatbelt_detector.get_inputs()[0].name
            output_name = self.seatbelt_detector.get_outputs()[0].name
            
            result = self.seatbelt_detector.run(
                [output_name],
                {input_name: input_tensor}
            )[0]
            
            no_seatbelt_confidence = float(result[0][0])
            
            if no_seatbelt_confidence > 0.7:
                return Incident(
                    incident_type='no_seatbelt',
                    track_id=vehicle.track_id,
                    confidence=no_seatbelt_confidence,
                    timestamp=timestamp,
                    frame_id=frame_id,
                    camera_id=camera_id,
                    bbox=vehicle.bbox,
                    metadata={
                        'vehicle_class': vehicle.class_name,
                        'plate': vehicle.plate_text
                    }
                )
        
        except Exception as e:
            self.logger.error(f"Seatbelt detection error: {e}")
        
        return None
    
    def _detect_wrong_way(
        self,
        vehicle,
        expected_flow: Tuple[float, float],
        camera_id: str,
        frame_id: int,
        timestamp: float
    ) -> Optional[Incident]:
        """Detect wrong-way driving"""
        
        # Get vehicle velocity
        vx, vy = vehicle.get_velocity()
        
        # Expected flow direction
        flow_x, flow_y = expected_flow
        
        # Calculate angle between velocity and expected flow
        dot_product = vx * flow_x + vy * flow_y
        mag_v = np.sqrt(vx**2 + vy**2)
        mag_flow = np.sqrt(flow_x**2 + flow_y**2)
        
        if mag_v < 5 or mag_flow < 1:  # Too slow to determine
            return None
        
        # Cosine similarity
        cos_angle = dot_product / (mag_v * mag_flow)
        
        # If angle > 90 degrees, vehicle is going opposite direction
        if cos_angle < -0.5:  # Going opposite
            return Incident(
                incident_type='wrong_way',
                track_id=vehicle.track_id,
                confidence=abs(cos_angle),
                timestamp=timestamp,
                frame_id=frame_id,
                camera_id=camera_id,
                bbox=vehicle.bbox,
                metadata={
                    'vehicle_class': vehicle.class_name,
                    'plate': vehicle.plate_text,
                    'velocity': (vx, vy),
                    'expected_flow': expected_flow
                }
            )
        
        return None
    
    def _detect_triple_riding(
        self,
        vehicle_roi: np.ndarray,
        vehicle,
        camera_id: str,
        frame_id: int,
        timestamp: float
    ) -> Optional[Incident]:
        """Detect triple riding on motorcycle"""
        
        # Use person detection to count riders
        # This is a simplified approach - in production, use trained model
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2GRAY)
            
            # Use HOG person detector (built into OpenCV)
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            
            # Detect people
            boxes, weights = hog.detectMultiScale(gray, winStride=(4, 4), padding=(8, 8), scale=1.05)
            
            # If 3 or more people detected on motorcycle
            if len(boxes) >= 3:
                return Incident(
                    incident_type='triple_riding',
                    track_id=vehicle.track_id,
                    confidence=min(1.0, len(boxes) / 3.0),
                    timestamp=timestamp,
                    frame_id=frame_id,
                    camera_id=camera_id,
                    bbox=vehicle.bbox,
                    metadata={
                        'vehicle_class': vehicle.class_name,
                        'plate': vehicle.plate_text,
                        'rider_count': len(boxes)
                    }
                )
        
        except Exception as e:
            self.logger.error(f"Triple riding detection error: {e}")
        
        return None
    
    def _preprocess_for_detection(
        self,
        image: np.ndarray,
        target_size: Tuple[int, int]
    ) -> np.ndarray:
        """Preprocess image for detection model"""
        
        # Resize
        resized = cv2.resize(image, target_size)
        
        # Normalize
        normalized = resized.astype(np.float32) / 255.0
        
        # Convert to RGB if needed
        if len(normalized.shape) == 2:
            normalized = cv2.cvtColor(normalized, cv2.COLOR_GRAY2RGB)
        
        # HWC to NCHW
        transposed = np.transpose(normalized, (2, 0, 1))
        
        # Add batch dimension
        batched = np.expand_dims(transposed, axis=0)
        
        return batched