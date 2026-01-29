"""Thread-safe circular frame buffer"""

import threading
import time
from collections import deque
from typing import Optional, Dict, Any
import numpy as np
import psutil
import logging

from ..core.frame import Frame

class FrameBuffer:
    """
    Thread-safe circular buffer for frames
    
    Features:
    - Memory management
    - Overflow protection
    - Automatic old frame dropping
    - Thread-safe operations
    """
    
    def __init__(
        self,
        camera_id: str,
        max_size: int = 30,
        max_memory_mb: int = 500
    ):
        """
        Initialize frame buffer
        
        Args:
            camera_id: Camera identifier
            max_size: Maximum number of frames to store
            max_memory_mb: Maximum memory usage in MB
        """
        self.camera_id = camera_id
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb
        
        self._buffer: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()
        
        # Statistics
        self._frame_counter = 0
        self._dropped_frames = 0
        self._total_bytes = 0
        
        self.logger = logging.getLogger(f"FrameBuffer.{camera_id}")
    
    def put(self, frame_data: np.ndarray, metadata: Dict = None) -> bool:
        """
        Add frame to buffer
        
        Args:
            frame_data: Frame as numpy array
            metadata: Optional metadata dictionary
            
        Returns:
            bool: True if added successfully, False if dropped
        """
        # Check memory usage before adding
        if not self._check_memory():
            self.logger.warning("Memory limit reached, dropping frame")
            self._dropped_frames += 1
            return False
        
        with self._lock:
            try:
                frame_obj = Frame(
                    camera_id=self.camera_id,
                    timestamp=time.time(),
                    frame_id=self._frame_counter,
                    image=frame_data,
                    metadata=metadata or {}
                )
                
                # Add to buffer (automatically drops oldest if full)
                if len(self._buffer) >= self.max_size:
                    dropped = self._buffer.popleft()
                    self._dropped_frames += 1
                    self.logger.debug(f"Buffer full, dropped frame {dropped.frame_id}")
                
                self._buffer.append(frame_obj)
                self._frame_counter += 1
                
                # Update byte count
                self._total_bytes += frame_data.nbytes
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error adding frame to buffer: {e}")
                self._dropped_frames += 1
                return False
    
    def get(self, block: bool = False, timeout: float = 1.0) -> Optional[Frame]:
        """
        Get oldest frame from buffer
        
        Args:
            block: If True, wait for frame to become available
            timeout: Maximum time to wait in seconds
            
        Returns:
            Optional[Frame]: Frame object or None
        """
        start_time = time.time()
        
        while True:
            with self._lock:
                if len(self._buffer) > 0:
                    frame = self._buffer.popleft()
                    # Update byte count
                    self._total_bytes -= frame.image.nbytes
                    return frame
            
            if not block:
                return None
            
            if time.time() - start_time > timeout:
                return None
            
            time.sleep(0.001)  # 1ms sleep to avoid busy waiting
    
    def peek(self) -> Optional[Frame]:
        """
        Peek at oldest frame without removing it
        
        Returns:
            Optional[Frame]: Frame object or None
        """
        with self._lock:
            if len(self._buffer) > 0:
                return self._buffer[0]
            return None
    
    def size(self) -> int:
        """Get current buffer size"""
        with self._lock:
            return len(self._buffer)
    
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        return self.size() == 0
    
    def is_full(self) -> bool:
        """Check if buffer is full"""
        return self.size() >= self.max_size
    
    def clear(self) -> None:
        """Clear all frames from buffer"""
        with self._lock:
            self._buffer.clear()
            self._total_bytes = 0
            self.logger.info("Buffer cleared")
    
    def _check_memory(self) -> bool:
        """
        Check if we're within memory limits
        
        Returns:
            bool: True if within limits
        """
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb < self.max_memory_mb
        except:
            # If we can't check memory, allow the operation
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get buffer statistics
        
        Returns:
            Dict: Statistics dictionary
        """
        with self._lock:
            total_frames = self._frame_counter
            drop_rate = (
                self._dropped_frames / max(1, total_frames)
                if total_frames > 0 else 0.0
            )
            
            return {
                "camera_id": self.camera_id,
                "buffer_size": len(self._buffer),
                "max_size": self.max_size,
                "total_frames": total_frames,
                "dropped_frames": self._dropped_frames,
                "drop_rate": drop_rate,
                "memory_mb": self._total_bytes / 1024 / 1024,
                "is_full": self.is_full(),
                "is_empty": self.is_empty()
            }
    
    def __len__(self) -> int:
        """Get buffer size using len()"""
        return self.size()
    
    def __repr__(self) -> str:
        return (f"FrameBuffer(camera_id='{self.camera_id}', "
                f"size={self.size()}/{self.max_size}, "
                f"dropped={self._dropped_frames})")