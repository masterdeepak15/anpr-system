"""RTSP stream reader with auto-reconnection"""

import cv2
import threading
import time
from typing import Optional, Dict, Any
import logging
import numpy as np

from ..core.interfaces import IStreamSource

class RTSPStreamReader(IStreamSource):
    """
    Production-grade RTSP stream reader
    
    Features:
    - Auto-reconnection on failure
    - Frame dropping under load
    - Thread-safe operation
    - Connection health monitoring
    """
    
    def __init__(
        self,
        camera_id: str,
        rtsp_url: str,
        reconnect_interval: int = 5,
        frame_skip: int = 2,
        max_reconnect_attempts: int = -1,  # -1 = infinite
        timeout: int = 10
    ):
        """
        Initialize RTSP stream reader
        
        Args:
            camera_id: Unique camera identifier
            rtsp_url: RTSP stream URL
            reconnect_interval: Seconds between reconnection attempts
            frame_skip: Number of frames to skip (for performance)
            max_reconnect_attempts: Max reconnect attempts (-1 for infinite)
            timeout: Connection timeout in seconds
        """
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.reconnect_interval = reconnect_interval
        self.frame_skip = frame_skip
        self.max_reconnect_attempts = max_reconnect_attempts
        self.timeout = timeout
        
        self._cap: Optional[cv2.VideoCapture] = None
        self._is_connected = False
        self._stop_flag = threading.Event()
        self._lock = threading.Lock()
        
        # Statistics
        self._frame_count = 0
        self._reconnect_count = 0
        self._last_frame_time = 0.0
        self._fps = 0.0
        self._error_count = 0
        
        self.logger = logging.getLogger(f"RTSPReader.{camera_id}")
    
    def connect(self) -> bool:
        """Establish RTSP connection with retry logic"""
        with self._lock:
            try:
                self.logger.info(f"Connecting to {self.rtsp_url}")
                
                # Create VideoCapture with RTSP backend
                self._cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                
                # Set buffer size to 1 to get latest frame
                self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # Set timeout
                self._cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, self.timeout * 1000)
                
                # Try to read a frame to verify connection
                ret, frame = self._cap.read()
                
                if ret and frame is not None:
                    self._is_connected = True
                    self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 25.0
                    self._error_count = 0
                    
                    self.logger.info(
                        f"Connected successfully - FPS: {self._fps:.1f}, "
                        f"Resolution: {frame.shape[1]}x{frame.shape[0]}"
                    )
                    return True
                else:
                    self.logger.warning("Connection established but no frames received")
                    if self._cap:
                        self._cap.release()
                    self._cap = None
                    return False
                    
            except Exception as e:
                self.logger.error(f"Connection failed: {e}")
                if self._cap:
                    self._cap.release()
                self._cap = None
                return False
    
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read frame with automatic frame skipping
        
        Returns:
            Optional[np.ndarray]: Frame if successful, None otherwise
        """
        if not self.is_connected():
            if not self._attempt_reconnect():
                return None
        
        with self._lock:
            if self._cap is None:
                return None
            
            try:
                # Skip frames to reduce CPU load
                for _ in range(self.frame_skip):
                    self._cap.grab()
                
                # Read the actual frame
                ret, frame = self._cap.read()
                
                if ret and frame is not None:
                    self._frame_count += 1
                    current_time = time.time()
                    
                    # Calculate actual FPS
                    if self._last_frame_time > 0:
                        delta = current_time - self._last_frame_time
                        if delta > 0:
                            self._fps = 0.9 * self._fps + 0.1 * (1.0 / delta)
                    
                    self._last_frame_time = current_time
                    self._error_count = 0
                    
                    return frame
                else:
                    self._error_count += 1
                    
                    if self._error_count > 5:
                        self.logger.warning(
                            f"Multiple frame read failures ({self._error_count}), "
                            "marking disconnected"
                        )
                        self._is_connected = False
                    
                    return None
                    
            except Exception as e:
                self.logger.error(f"Frame read error: {e}")
                self._error_count += 1
                self._is_connected = False
                return None
    
    def is_connected(self) -> bool:
        """Check if stream is connected"""
        with self._lock:
            return self._is_connected
    
    def disconnect(self) -> None:
        """Clean shutdown"""
        self.logger.info("Disconnecting...")
        self._stop_flag.set()
        
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
            self._is_connected = False
        
        self.logger.info("Disconnected")
    
    def get_fps(self) -> float:
        """Get current FPS"""
        with self._lock:
            return self._fps
    
    def _attempt_reconnect(self) -> bool:
        """Internal reconnection logic"""
        if (self.max_reconnect_attempts >= 0 and 
            self._reconnect_count >= self.max_reconnect_attempts):
            self.logger.error("Max reconnection attempts reached")
            return False
        
        self.logger.info(
            f"Attempting reconnection "
            f"(attempt {self._reconnect_count + 1})"
        )
        
        time.sleep(self.reconnect_interval)
        
        success = self.connect()
        
        if success:
            self._reconnect_count = 0
            self.logger.info("Reconnection successful")
        else:
            self._reconnect_count += 1
            self.logger.warning(f"Reconnection failed (attempt {self._reconnect_count})")
        
        return success
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stream statistics"""
        with self._lock:
            return {
                "camera_id": self.camera_id,
                "connected": self._is_connected,
                "frame_count": self._frame_count,
                "fps": self._fps,
                "reconnect_count": self._reconnect_count,
                "error_count": self._error_count,
                "rtsp_url": self.rtsp_url
            }
    
    def __repr__(self) -> str:
        return (f"RTSPStreamReader(camera_id='{self.camera_id}', "
                f"connected={self._is_connected}, "
                f"fps={self._fps:.1f})")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()