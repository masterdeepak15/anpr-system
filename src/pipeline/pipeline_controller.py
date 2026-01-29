"""Main pipeline controller - orchestrates entire ANPR workflow"""

import threading
import time
import signal
import sys
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import logging
import multiprocessing

from ..core.frame import Frame
from ..core.result import PlateResult
from ..stream.rtsp_reader import RTSPStreamReader
from ..stream.frame_buffer import FrameBuffer
from ..preprocessing.frame_preprocessor import FramePreprocessor
from ..detection.vehicle_detector import VehicleDetector
from ..detection.plate_detector import PlateDetector
from ..enhancement.plate_enhancer import PlateEnhancer
from ..ocr.custom_ocr import CustomOCREngine
from ..validation.validation_engine import ValidationEngine
from ..aggregation.result_aggregator import ResultAggregator
from ..tracking.vehicle_tracker import VehicleTracker
from ..tracking.incident_detector import IncidentDetector
from ..tracking.video_buffer import VideoBuffer

class PipelineController:
    """
    Main orchestrator for the entire ANPR pipeline
    
    Manages:
    - Multi-camera processing
    - Worker pool management
    - Error recovery
    - Graceful shutdown
    """
    
    def __init__(
        self,
        config_manager: 'ConfigManager',
        num_workers: int = None,
        enable_tracking: bool = True,
        enable_incident_detection: bool = True
    ):
        """
        Initialize pipeline controller
        
        Args:
            config_manager: Configuration manager instance
            num_workers: Number of worker threads (auto-detect if None)
            enable_tracking: Enable vehicle tracking
            enable_incident_detection: Enable incident detection
        """
        self.config_manager = config_manager
        
        # Auto-detect CPU cores if not specified
        if num_workers is None:
            num_workers = max(2, multiprocessing.cpu_count() - 1)
        
        self.num_workers = num_workers
        
        # Components (initialized later)
        self.stream_readers: Dict[str, RTSPStreamReader] = {}
        self.frame_buffers: Dict[str, FrameBuffer] = {}
        self.preprocessor: Optional[FramePreprocessor] = None
        self.vehicle_detector: Optional[VehicleDetector] = None
        self.plate_detector: Optional[PlateDetector] = None
        self.plate_enhancer: Optional[PlateEnhancer] = None
        self.ocr_engine: Optional[CustomOCREngine] = None
        self.result_aggregator: Optional[ResultAggregator] = None
        self.validation_engine: Optional[ValidationEngine] = None
        
        # Tracking components (initialized later)
        self.enable_tracking = enable_tracking
        self.enable_incident_detection = enable_incident_detection
        self.vehicle_trackers: Dict[str, VehicleTracker] = {}
        self.incident_detector: Optional[IncidentDetector] = None
        self.video_buffers: Dict[str, VideoBuffer] = {}


        # Worker pool
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        
        # Control flags
        self._running = False
        self._shutdown_event = threading.Event()
        
        # Statistics
        self._stats = {
            "total_frames_processed": 0,
            "total_plates_detected": 0,
            "total_errors": 0,
            "start_time": None
        }
        self._stats_lock = threading.Lock()
        
        # API server reference (set later)
        self.api_server = None
        
        self.logger = logging.getLogger("PipelineController")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self) -> bool:
        """Initialize all pipeline components"""
        try:
            self.logger.info("Initializing pipeline components...")
            
            # 1. Load configuration
            config = self.config_manager.get_config()
            
            # 2. Initialize preprocessor
            self.preprocessor = FramePreprocessor(
                target_width=config.get("frame_width", 640),
                target_height=config.get("frame_height", 480),
                normalize=True
            )
            
            # 3. Initialize detectors
            self.vehicle_detector = VehicleDetector(
                model_path=config.get("vehicle_model_path"),
                confidence_threshold=config.get("vehicle_confidence", 0.5)
            )
            
            self.plate_detector = PlateDetector(
                model_path=config.get("plate_model_path"),
                use_ml_model=config.get("use_plate_ml", True)
            )
            
            # 4. Initialize enhancer
            self.plate_enhancer = PlateEnhancer()
            
            # 5. Initialize OCR
            self.ocr_engine = CustomOCREngine(
                classifier_model_path=config.get("ocr_model_path"),
                country_code=config.get("country_code", "IN")
            )
            
            # 6. Initialize aggregator and validator
            self.result_aggregator = ResultAggregator(
                window_size=config.get("aggregation_window", 5),
                min_occurrences=config.get("min_occurrences", 3)
            )
            
            self.validation_engine = ValidationEngine(
                country_code=config.get("country_code", "IN")
            )
            
            # 7. Initialize worker pool
            self._thread_pool = ThreadPoolExecutor(max_workers=self.num_workers * 2)
            
            # 8. Initialize cameras
            cameras = self.config_manager.get_cameras()
            for camera in cameras:
                self._init_camera(camera)
            
            # 9. Initialize tracking components
            if self.enable_tracking:
                for camera in cameras:
                    camera_id = camera["camera_id"]
                    self.vehicle_trackers[camera_id] = VehicleTracker(
                        max_disappeared=30,
                        iou_threshold=0.3
                    )
                    
                    # Initialize video buffer for each camera
                    self.video_buffers[camera_id] = VideoBuffer(
                        camera_id=camera_id,
                        buffer_seconds=10,
                        fps=config.get("target_fps", 5.0),
                        output_dir="incidents"
                    )
            
            # 10. Initialize incident detector
            if self.enable_incident_detection:
                self.incident_detector = IncidentDetector(
                    helmet_model_path=config.get("helmet_model_path"),
                    seatbelt_model_path=config.get("seatbelt_model_path"),
                    enable_helmet_detection=config.get("enable_helmet_detection", True),
                    enable_seatbelt_detection=config.get("enable_seatbelt_detection", True),
                    enable_wrong_way_detection=config.get("enable_wrong_way_detection", True),
                    enable_triple_riding_detection=config.get("enable_triple_riding_detection", True)
                )
        
            self.logger.info(f"Pipeline initialization complete ({self.num_workers} workers)")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}", exc_info=True)
            return False
    
    def _init_camera(self, camera_config: Dict) -> bool:
        """Initialize a single camera"""
        try:
            camera_id = camera_config["camera_id"]
            rtsp_url = camera_config["rtsp_url"]
            
            self.logger.info(f"Initializing camera: {camera_id}")
            
            # Create stream reader
            reader = RTSPStreamReader(
                camera_id=camera_id,
                rtsp_url=rtsp_url,
                frame_skip=camera_config.get("frame_skip", 2)
            )
            
            # Create frame buffer
            buffer = FrameBuffer(
                camera_id=camera_id,
                max_size=30
            )
            
            # Connect
            if not reader.connect():
                self.logger.error(f"Failed to connect camera: {camera_id}")
                return False
            
            self.stream_readers[camera_id] = reader
            self.frame_buffers[camera_id] = buffer
            
            self.logger.info(f"Camera initialized: {camera_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Camera init failed: {e}")
            return False
    
    def start(self) -> None:
        """Start the pipeline"""
        if self._running:
            self.logger.warning("Pipeline already running")
            return
        
        self._running = True
        self._shutdown_event.clear()
        
        with self._stats_lock:
            self._stats["start_time"] = time.time()
        
        self.logger.info("Starting pipeline...")
        
        # Start frame capture threads for each camera
        for camera_id in self.stream_readers.keys():
            self._thread_pool.submit(self._capture_loop, camera_id)
        
        # Start processing workers
        for i in range(self.num_workers):
            self._thread_pool.submit(self._processing_worker, i)
        
        self.logger.info("Pipeline started successfully")
    
    def stop(self) -> None:
        """Stop the pipeline gracefully"""
        self.logger.info("Stopping pipeline...")
        
        self._running = False
        self._shutdown_event.set()
        
        # Disconnect cameras
        for reader in self.stream_readers.values():
            reader.disconnect()
        
        # Shutdown worker pool
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
        
        self.logger.info("Pipeline stopped")
    
    def _capture_loop(self, camera_id: str) -> None:
        """
        Frame capture loop for a single camera
        Runs in a separate thread
        """
        reader = self.stream_readers[camera_id]
        buffer = self.frame_buffers[camera_id]
        
        self.logger.info(f"Capture loop started for {camera_id}")
        
        while self._running and not self._shutdown_event.is_set():
            try:
                # Read frame
                frame = reader.read_frame()
                
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Add to buffer
                success = buffer.put(frame, metadata={"camera_id": camera_id})
                
                if not success:
                    self.logger.debug(f"Buffer full for {camera_id}, frame dropped")
                
            except Exception as e:
                self.logger.error(f"Capture error for {camera_id}: {e}")
                time.sleep(1.0)
        
        self.logger.info(f"Capture loop stopped for {camera_id}")
    
    def _processing_worker(self, worker_id: int) -> None:
        """
        Processing worker - processes frames from all cameras
        Runs in a separate thread
        """
        self.logger.info(f"Processing worker {worker_id} started")
        
        while self._running and not self._shutdown_event.is_set():
            try:
                # Round-robin through cameras
                processed_any = False
                
                for camera_id, buffer in self.frame_buffers.items():
                    frame_obj = buffer.get(block=False)
                    
                    if frame_obj is not None:
                        self._process_frame(frame_obj)
                        processed_any = True
                
                # Sleep briefly if no frames to process
                if not processed_any:
                    time.sleep(0.01)
                    
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
                with self._stats_lock:
                    self._stats["total_errors"] += 1
        
        self.logger.info(f"Processing worker {worker_id} stopped")
    
    def _process_frame(self, frame_obj: Frame) -> None:
        """
        Process a single frame through the entire pipeline
        """
        try:
            start_time = time.time()
            camera_id = frame_obj.camera_id
            
            # Add frame to video buffer
            if camera_id in self.video_buffers:
                self.video_buffers[camera_id].add_frame(
                    frame_obj.image,
                    frame_obj.timestamp
                )
            
            # 1. Preprocess
            processed_frame = self.preprocessor.process(frame_obj.image)
            
            # 2. Vehicle detection
            vehicle_detections = self.vehicle_detector.detect(processed_frame)
            
            if len(vehicle_detections) == 0:
                return
            
            # Convert detections to dictionary format for tracker
            detection_dicts = []
            for det in vehicle_detections:
                detection_dicts.append({
                    'bbox': det.bbox,
                    'confidence': det.confidence,
                    'class_name': det.class_name,
                    'class_id': det.class_id
                })
            
            # 3. Update tracker
            tracked_vehicles = {}
            if self.enable_tracking and camera_id in self.vehicle_trackers:
                tracked_vehicles = self.vehicle_trackers[camera_id].update(
                    detection_dicts,
                    frame_obj.timestamp
                )
            
            # 4. Detect incidents
            incidents = []
            if self.enable_incident_detection and self.incident_detector:
                # Get expected flow direction from config (if available)
                flow_direction = self._get_flow_direction(camera_id)
                
                incidents = self.incident_detector.detect_incidents(
                    frame_obj.image,
                    tracked_vehicles,
                    camera_id,
                    frame_obj.frame_id,
                    frame_obj.timestamp,
                    flow_direction
                )
            
            # 5. Handle detected incidents
            for incident in incidents:
                self._handle_incident(incident, frame_obj)
            
            # 6. Process each vehicle for plate detection
            for vehicle_det in vehicle_detections:
                # Extract vehicle ROI
                vehicle_roi = self.preprocessor.extract_roi(
                    frame_obj.image,
                    vehicle_det.bbox
                )
                
                # Plate detection
                plate_detections = self.plate_detector.detect(vehicle_roi)
                
                if len(plate_detections) == 0:
                    continue
                
                # Process best plate candidate
                best_plate = max(plate_detections, key=lambda p: p.confidence)
                
                # Extract plate ROI (relative to vehicle ROI)
                x1, y1, x2, y2 = best_plate.bbox
                plate_roi = vehicle_roi[int(y1):int(y2), int(x1):int(x2)]
                
                if plate_roi.size == 0:
                    continue
                
                # Enhance plate
                enhanced_plate = self.plate_enhancer.process(plate_roi)
                
                # OCR
                ocr_result = self.ocr_engine.recognize(enhanced_plate)
                
                # Update metadata
                ocr_result.camera_id = frame_obj.camera_id
                ocr_result.frame_id = frame_obj.frame_id
                ocr_result.timestamp = frame_obj.timestamp
                
                # Validate
                is_valid = self.validation_engine.validate(ocr_result.plate_text)
                
                if not is_valid:
                    self.logger.debug(f"Invalid plate rejected: {ocr_result.plate_text}")
                    continue
                
                # Update tracked vehicle with plate info
                if self.enable_tracking:
                    self._update_vehicle_plate(
                        camera_id,
                        vehicle_det.bbox,
                        ocr_result.plate_text
                    )
                
                # Aggregate
                finalized_result = self.result_aggregator.add_result(ocr_result)
                
                if finalized_result:
                    self._handle_finalized_result(finalized_result)
            
            # Update stats
            with self._stats_lock:
                self._stats["total_frames_processed"] += 1
            
            # Log performance
            processing_time = (time.time() - start_time) * 1000
            self.logger.debug(
                f"Frame {frame_obj.frame_id} processed in {processing_time:.2f}ms"
            )
            
        except Exception as e:
            self.logger.error(f"Frame processing error: {e}", exc_info=True)
            with self._stats_lock:
                self._stats["total_errors"] += 1
    
    def _handle_finalized_result(self, result: PlateResult) -> None:
        """Handle a finalized plate result"""
        try:
            # Save to database
            self.config_manager.save_result(result)
            
            # Update stats
            with self._stats_lock:
                self._stats["total_plates_detected"] += 1
            
            # Broadcast to API subscribers
            if self.api_server:
                self.api_server.broadcast_event('plate_detected', {
                    "camera_id": result.camera_id,
                    "plate_text": result.plate_text,
                    "confidence": result.confidence,
                    "timestamp": result.timestamp
                })
            
            self.logger.info(
                f"✓ Plate detected: {result.plate_text} "
                f"(confidence: {result.confidence:.2f}, camera: {result.camera_id})"
            )
            
        except Exception as e:
            self.logger.error(f"Result handling error: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        with self._stats_lock:
            stats = self._stats.copy()
        
        if stats["start_time"]:
            uptime = time.time() - stats["start_time"]
            stats["uptime_seconds"] = uptime
            stats["avg_fps"] = stats["total_frames_processed"] / uptime if uptime > 0 else 0
        
        # Add per-camera stats
        camera_stats = {}
        for camera_id in self.stream_readers.keys():
            camera_stats[camera_id] = {
                "stream": self.stream_readers[camera_id].get_stats(),
                "buffer": self.frame_buffers[camera_id].get_stats()
            }
        
        stats["cameras"] = camera_stats
        
        return stats
    
    def set_api_server(self, api_server) -> None:
        """Set API server reference for event broadcasting"""
        self.api_server = api_server
        self.logger.info("API server linked to pipeline")
    
    def _get_flow_direction(self, camera_id: str) -> Optional[Tuple[float, float]]:
        """Get expected traffic flow direction for camera"""
        # This could be loaded from camera configuration
        # For now, return None (incidents will be detected without flow checking)
        # Example: return (1.0, 0.0) for left-to-right flow
        
        camera_flow_config = {
            # "cam_entrance_01": (0.0, 1.0),  # top-to-bottom
            # "cam_exit_01": (0.0, -1.0),     # bottom-to-top
        }
        
        return camera_flow_config.get(camera_id)

    def _update_vehicle_plate(
        self,
        camera_id: str,
        vehicle_bbox: Tuple,
        plate_text: str
    ) -> None:
        """Update tracked vehicle with detected plate"""
        if camera_id not in self.vehicle_trackers:
            return
        
        tracker = self.vehicle_trackers[camera_id]
        
        # Find matching tracked vehicle
        for track_id, vehicle in tracker.tracked_vehicles.items():
            # Check if bboxes overlap
            iou = self._calculate_iou(vehicle_bbox, vehicle.bbox)
            if iou > 0.5:
                vehicle.plate_text = plate_text
                break

    def _calculate_iou(self, bbox1: Tuple, bbox2: Tuple) -> float:
        """Calculate IoU between two bounding boxes"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Intersection
        x_left = max(x1_1, x1_2)
        y_top = max(y1_1, y1_2)
        x_right = min(x2_1, x2_2)
        y_bottom = min(y2_1, y2_2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        
        # Union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0

    def _handle_incident(self, incident, frame_obj: Frame) -> None:
        """Handle detected incident"""
        try:
            camera_id = incident.camera_id
            
            # Log incident
            self.logger.warning(
                f"🚨 INCIDENT DETECTED: {incident.incident_type} "
                f"(Track #{incident.track_id}, Camera: {camera_id}, "
                f"Confidence: {incident.confidence:.2f})"
            )
            
            # Save to database
            self.config_manager.save_incident(incident)
            
            # Save video clip in background thread
            if camera_id in self.video_buffers:
                video_thread = threading.Thread(
                    target=self._save_incident_video,
                    args=(camera_id, incident),
                    daemon=True
                )
                video_thread.start()
            
            # Broadcast to API subscribers
            if self.api_server:
                self.api_server.broadcast_event('incident_detected', {
                    'incident_type': incident.incident_type,
                    'track_id': incident.track_id,
                    'camera_id': incident.camera_id,
                    'confidence': incident.confidence,
                    'timestamp': incident.timestamp,
                    'metadata': incident.metadata
                })
            
            # Update statistics
            with self._stats_lock:
                if "total_incidents" not in self._stats:
                    self._stats["total_incidents"] = 0
                self._stats["total_incidents"] += 1
            
        except Exception as e:
            self.logger.error(f"Incident handling error: {e}")

    def _save_incident_video(self, camera_id: str, incident) -> None:
        """Save incident video clip (runs in background)"""
        try:
            video_buffer = self.video_buffers[camera_id]
            
            # Save video (5 seconds before, 5 seconds after)
            video_path = video_buffer.save_incident_video(
                incident,
                before_seconds=5,
                after_seconds=5
            )
            
            if video_path:
                self.logger.info(f"Incident video saved: {video_path}")
                
                # Update incident record with video path
                self.config_manager.update_incident_video_path(
                    incident,
                    video_path
                )
        
        except Exception as e:
            self.logger.error(f"Video save error: {e}")

    def get_tracked_vehicles(self, camera_id: str = None) -> Dict:
        """Get currently tracked vehicles"""
        if camera_id:
            if camera_id in self.vehicle_trackers:
                return {
                    camera_id: self.vehicle_trackers[camera_id].get_all_tracks()
                }
            return {}
        
        # Return all tracked vehicles from all cameras
        all_tracks = {}
        for cam_id, tracker in self.vehicle_trackers.items():
            all_tracks[cam_id] = tracker.get_all_tracks()
        
        return all_tracks

    def __repr__(self) -> str:
        return f"PipelineController(workers={self.num_workers}, cameras={len(self.stream_readers)})"