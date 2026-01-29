"""Multi-object tracking for vehicles"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time
import logging

@dataclass
class TrackedVehicle:
    """Tracked vehicle object"""
    track_id: int
    class_name: str
    bbox: Tuple[int, int, int, int]
    confidence: float
    last_seen: float
    first_seen: float
    trajectory: List[Tuple[int, int]]  # List of center points
    frames_tracked: int
    plate_text: Optional[str] = None
    incidents: List[str] = None  # List of detected incidents
    
    def __post_init__(self):
        if self.incidents is None:
            self.incidents = []
    
    def get_center(self) -> Tuple[int, int]:
        """Get bounding box center"""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    def get_velocity(self) -> Tuple[float, float]:
        """Calculate velocity from trajectory"""
        if len(self.trajectory) < 2:
            return (0.0, 0.0)
        
        # Calculate velocity from last 2 positions
        p1 = self.trajectory[-2]
        p2 = self.trajectory[-1]
        
        vx = p2[0] - p1[0]
        vy = p2[1] - p1[1]
        
        return (vx, vy)
    
    def update(self, bbox: Tuple, confidence: float) -> None:
        """Update tracked vehicle"""
        self.bbox = bbox
        self.confidence = confidence
        self.last_seen = time.time()
        self.frames_tracked += 1
        
        # Add to trajectory
        center = self.get_center()
        self.trajectory.append(center)
        
        # Keep trajectory limited to last 30 points
        if len(self.trajectory) > 30:
            self.trajectory.pop(0)


class VehicleTracker:
    """
    Multi-object tracker using IoU-based matching
    
    Features:
    - Track vehicles across frames
    - Maintain trajectory history
    - Handle occlusions
    - Track ID management
    """
    
    def __init__(
        self,
        max_disappeared: int = 30,
        iou_threshold: float = 0.3
    ):
        """
        Initialize tracker
        
        Args:
            max_disappeared: Max frames before removing track
            iou_threshold: IoU threshold for matching
        """
        self.max_disappeared = max_disappeared
        self.iou_threshold = iou_threshold
        
        self.next_track_id = 1
        self.tracked_vehicles: Dict[int, TrackedVehicle] = {}
        
        self.logger = logging.getLogger("VehicleTracker")
    
    def update(
        self,
        detections: List[Dict],
        frame_time: float
    ) -> Dict[int, TrackedVehicle]:
        """
        Update tracker with new detections
        
        Args:
            detections: List of vehicle detections
            frame_time: Current frame timestamp
            
        Returns:
            Dict: Current tracked vehicles
        """
        # If no existing tracks, create new ones
        if len(self.tracked_vehicles) == 0:
            for det in detections:
                self._create_track(det, frame_time)
            return self.tracked_vehicles
        
        # If no detections, increment disappeared counter
        if len(detections) == 0:
            self._handle_disappeared(frame_time)
            return self.tracked_vehicles
        
        # Match detections to existing tracks
        matches, unmatched_tracks, unmatched_detections = self._match_detections(
            detections
        )
        
        # Update matched tracks
        for track_id, det_idx in matches:
            detection = detections[det_idx]
            self.tracked_vehicles[track_id].update(
                detection['bbox'],
                detection['confidence']
            )
        
        # Handle unmatched tracks
        for track_id in unmatched_tracks:
            track = self.tracked_vehicles[track_id]
            if frame_time - track.last_seen > self.max_disappeared:
                del self.tracked_vehicles[track_id]
                self.logger.debug(f"Removed track {track_id}")
        
        # Create new tracks for unmatched detections
        for det_idx in unmatched_detections:
            detection = detections[det_idx]
            self._create_track(detection, frame_time)
        
        return self.tracked_vehicles
    
    def _create_track(self, detection: Dict, frame_time: float) -> None:
        """Create new tracked vehicle"""
        track = TrackedVehicle(
            track_id=self.next_track_id,
            class_name=detection.get('class_name', 'vehicle'),
            bbox=detection['bbox'],
            confidence=detection['confidence'],
            last_seen=frame_time,
            first_seen=frame_time,
            trajectory=[],
            frames_tracked=1
        )
        
        # Initialize trajectory
        track.trajectory.append(track.get_center())
        
        self.tracked_vehicles[self.next_track_id] = track
        self.logger.debug(f"Created track {self.next_track_id}")
        
        self.next_track_id += 1
    
    def _match_detections(
        self,
        detections: List[Dict]
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """
        Match detections to existing tracks using IoU
        
        Returns:
            Tuple of (matches, unmatched_tracks, unmatched_detections)
        """
        track_ids = list(self.tracked_vehicles.keys())
        
        if len(track_ids) == 0 or len(detections) == 0:
            return [], track_ids, list(range(len(detections)))
        
        # Calculate IoU matrix
        iou_matrix = np.zeros((len(track_ids), len(detections)))
        
        for i, track_id in enumerate(track_ids):
            track_bbox = self.tracked_vehicles[track_id].bbox
            for j, detection in enumerate(detections):
                det_bbox = detection['bbox']
                iou_matrix[i, j] = self._calculate_iou(track_bbox, det_bbox)
        
        # Greedy matching (can be improved with Hungarian algorithm)
        matches = []
        matched_tracks = set()
        matched_detections = set()
        
        # Sort by IoU (highest first)
        indices = np.argsort(-iou_matrix.flatten())
        
        for idx in indices:
            i = idx // len(detections)
            j = idx % len(detections)
            
            if iou_matrix[i, j] < self.iou_threshold:
                break
            
            if i not in matched_tracks and j not in matched_detections:
                matches.append((track_ids[i], j))
                matched_tracks.add(i)
                matched_detections.add(j)
        
        # Unmatched tracks and detections
        unmatched_tracks = [
            track_ids[i] for i in range(len(track_ids))
            if i not in matched_tracks
        ]
        
        unmatched_detections = [
            j for j in range(len(detections))
            if j not in matched_detections
        ]
        
        return matches, unmatched_tracks, unmatched_detections
    
    def _calculate_iou(
        self,
        bbox1: Tuple[int, int, int, int],
        bbox2: Tuple[int, int, int, int]
    ) -> float:
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
    
    def _handle_disappeared(self, frame_time: float) -> None:
        """Handle tracks that didn't match any detection"""
        to_remove = []
        
        for track_id, track in self.tracked_vehicles.items():
            if frame_time - track.last_seen > self.max_disappeared:
                to_remove.append(track_id)
        
        for track_id in to_remove:
            del self.tracked_vehicles[track_id]
    
    def get_track(self, track_id: int) -> Optional[TrackedVehicle]:
        """Get tracked vehicle by ID"""
        return self.tracked_vehicles.get(track_id)
    
    def get_all_tracks(self) -> Dict[int, TrackedVehicle]:
        """Get all active tracks"""
        return self.tracked_vehicles
    
    def clear(self) -> None:
        """Clear all tracks"""
        self.tracked_vehicles.clear()
        self.next_track_id = 1