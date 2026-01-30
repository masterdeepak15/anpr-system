"""Circular video buffer for incident recording"""

import cv2
import numpy as np
from collections import deque
from typing import Optional, List, Dict
import threading
import time
from pathlib import Path
import logging

class VideoBuffer:
    """
    Circular video buffer for continuous recording
    
    Maintains a rolling buffer of frames to capture
    video before and after incidents
    """
    
    def __init__(
        self,
        camera_id: str,
        buffer_seconds: int = 10,
        fps: float = 5.0,
        output_dir: str = "incidents"
    ):
        """
        Initialize video buffer
        
        Args:
            camera_id: Camera identifier
            buffer_seconds: Seconds to buffer
            fps: Frames per second
            output_dir: Output directory for saved videos
        """
        self.camera_id = camera_id
        self.buffer_seconds = buffer_seconds
        self.fps = fps
        self.output_dir = Path(output_dir)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate buffer size
        self.max_frames = int(buffer_seconds * fps)
        
        # Circular buffer
        self.buffer: deque = deque(maxlen=self.max_frames)
        self._lock = threading.Lock()
        
        # Recording state
        self.is_recording = False
        self.record_start_time = None
        self.record_incident_id = None
        
        self.logger = logging.getLogger(f"VideoBuffer.{camera_id}")
    
    def add_frame(self, frame: np.ndarray, timestamp: float) -> None:
        """
        Add frame to circular buffer
        
        Args:
            frame: Frame image
            timestamp: Frame timestamp
        """
        with self._lock:
            self.buffer.append({
                'frame': frame.copy(),
                'timestamp': timestamp
            })
    
    def save_incident_video(
        self,
        incident,
        before_seconds: int = 5,
        after_seconds: int = 5
    ) -> Optional[str]:
        """
        Save video clip of incident
        
        Args:
            incident: Incident object
            before_seconds: Seconds before incident
            after_seconds: Seconds after incident
            
        Returns:
            str: Path to saved video file
        """
        
        # Start recording future frames
        self._start_recording(incident, after_seconds)
        
        # Get frames before incident
        incident_time = incident.timestamp
        before_frames = self._get_frames_before(incident_time, before_seconds)
        
        if len(before_frames) == 0:
            self.logger.warning(f"No frames available before incident")
            return None
        
        # Wait for after frames to be recorded
        time.sleep(after_seconds + 1)
        
        # Get all frames (before + during + after)
        all_frames = self._get_all_frames_for_incident(
            incident_time,
            before_seconds,
            after_seconds
        )
        
        if len(all_frames) == 0:
            self.logger.error("No frames to save")
            return None
        
        # Save video
        video_path = self._save_video_file(incident, all_frames)
        
        # Save snapshot image
        self._save_snapshot_image(incident, all_frames[len(before_frames)])
        
        return video_path
    
    def _get_frames_before(
        self,
        incident_time: float,
        seconds: int
    ) -> List[Dict]:
        """Get frames before incident"""
        with self._lock:
            cutoff_time = incident_time - seconds
            
            frames = [
                f for f in self.buffer
                if f['timestamp'] >= cutoff_time and f['timestamp'] <= incident_time
            ]
            
            return frames
    
    def _get_all_frames_for_incident(
        self,
        incident_time: float,
        before_seconds: int,
        after_seconds: int
    ) -> List[Dict]:
        """Get all frames for incident video"""
        with self._lock:
            start_time = incident_time - before_seconds
            end_time = incident_time + after_seconds
            
            frames = [
                f for f in self.buffer
                if start_time <= f['timestamp'] <= end_time
            ]
            
            return frames
    
    def _start_recording(self, incident, duration: int) -> None:
        """Start recording future frames"""
        self.is_recording = True
        self.record_start_time = time.time()
        self.record_incident_id = f"{incident.camera_id}_{incident.track_id}_{int(incident.timestamp)}"
    
    def _save_video_file(self, incident, frames: List[Dict]) -> str:
        """Save frames as video file"""
        
        # Generate filename
        incident_id = f"{incident.camera_id}_{incident.incident_type}_{incident.track_id}_{int(incident.timestamp)}"
        video_filename = f"{incident_id}.mp4"
        video_path = self.output_dir / video_filename
        
        if len(frames) == 0:
            return None
        
        # Get frame dimensions
        frame_height, frame_width = frames[0]['frame'].shape[:2]
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(
            str(video_path),
            fourcc,
            self.fps,
            (frame_width, frame_height)
        )
        
        # Write frames
        for frame_data in frames:
            frame = frame_data['frame']
            
            # Add timestamp overlay
            timestamp_text = time.strftime(
                '%Y-%m-%d %H:%M:%S',
                time.localtime(frame_data['timestamp'])
            )
            
            cv2.putText(
                frame,
                timestamp_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            
            # Add incident info overlay
            incident_text = f"{incident.incident_type.upper()} - Track #{incident.track_id}"
            cv2.putText(
                frame,
                incident_text,
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
            
            writer.write(frame)
        
        writer.release()
        
        self.logger.info(f"Saved incident video: {video_path}")
        
        return str(video_path)
    
    def _save_snapshot_image(self, incident, frame_data: Dict) -> str:
        """Save snapshot image at incident moment"""
        
        incident_id = f"{incident.camera_id}_{incident.incident_type}_{incident.track_id}_{int(incident.timestamp)}"
        image_filename = f"{incident_id}.jpg"
        image_path = self.output_dir / image_filename
        
        frame = frame_data['frame'].copy()
        
        # Draw bounding box
        x1, y1, x2, y2 = incident.bbox
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 3)
        
        # Add text
        cv2.putText(
            frame,
            f"{incident.incident_type.upper()}",
            (int(x1), int(y1) - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )
        
        cv2.imwrite(str(image_path), frame)
        
        self.logger.info(f"Saved incident snapshot: {image_path}")
        
        return str(image_path)
    
    def get_buffer_stats(self) -> Dict:
        """Get buffer statistics"""
        with self._lock:
            return {
                'camera_id': self.camera_id,
                'buffer_size': len(self.buffer),
                'max_frames': self.max_frames,
                'buffer_seconds': self.buffer_seconds,
                'fps': self.fps
            }
