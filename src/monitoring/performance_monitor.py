"""Performance monitoring and optimization"""

import psutil
import threading
import time
import numpy as np
from typing import Dict, Any, List
from dataclasses import dataclass
import logging

@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    fps_per_camera: Dict[str, float]
    processing_time_ms: float
    queue_sizes: Dict[str, int]
    dropped_frames: int

class PerformanceMonitor:
    """
    Monitor and optimize system performance
    
    Features:
    - Adaptive frame skipping
    - Dynamic worker scaling
    - Bottleneck detection
    - Performance alerts
    """
    
    def __init__(
        self,
        pipeline,
        target_fps: float = 5.0,
        max_cpu_percent: float = 80.0,
        max_memory_mb: float = 2000.0
    ):
        """
        Initialize performance monitor
        
        Args:
            pipeline: Pipeline controller
            target_fps: Target FPS per camera
            max_cpu_percent: Maximum CPU usage
            max_memory_mb: Maximum memory usage
        """
        self.pipeline = pipeline
        self.target_fps = target_fps
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_mb = max_memory_mb
        
        self._metrics_history: List[PerformanceMetrics] = []
        self._monitoring = False
        self._monitor_thread = None
        
        self.logger = logging.getLogger("PerformanceMonitor")
    
    def start_monitoring(self) -> None:
        """Start performance monitoring"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
        
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self._monitoring:
            try:
                metrics = self._collect_metrics()
                self._metrics_history.append(metrics)
                
                # Keep only last 100 samples
                if len(self._metrics_history) > 100:
                    self._metrics_history.pop(0)
                
                # Check for issues
                self._check_performance_issues(metrics)
                
                # Adaptive optimization
                self._adaptive_optimize(metrics)
                
                time.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        process = psutil.Process()
        
        cpu_percent = process.cpu_percent(interval=1)
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        # FPS per camera
        fps_per_camera = {}
        for camera_id, reader in self.pipeline.stream_readers.items():
            fps_per_camera[camera_id] = reader.get_fps()
        
        # Queue sizes
        queue_sizes = {}
        dropped_frames = 0
        for camera_id, buffer in self.pipeline.frame_buffers.items():
            stats = buffer.get_stats()
            queue_sizes[camera_id] = stats['buffer_size']
            dropped_frames += stats['dropped_frames']
        
        # Processing time (simplified)
        processing_time_ms = 0.0
        if self.pipeline.vehicle_detector:
            processing_time_ms = self.pipeline.vehicle_detector.get_inference_time()
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            fps_per_camera=fps_per_camera,
            processing_time_ms=processing_time_ms,
            queue_sizes=queue_sizes,
            dropped_frames=dropped_frames
        )
    
    def _check_performance_issues(self, metrics: PerformanceMetrics) -> None:
        """Check for performance issues"""
        if metrics.cpu_percent > self.max_cpu_percent:
            self.logger.warning(
                f"High CPU usage: {metrics.cpu_percent:.1f}% "
                f"(threshold: {self.max_cpu_percent}%)"
            )
        
        if metrics.memory_mb > self.max_memory_mb:
            self.logger.warning(
                f"High memory usage: {metrics.memory_mb:.1f}MB "
                f"(threshold: {self.max_memory_mb}MB)"
            )
    
    def _adaptive_optimize(self, metrics: PerformanceMetrics) -> None:
        """Adaptive optimization based on performance"""
        # Increase frame skip if CPU high
        if metrics.cpu_percent > self.max_cpu_percent * 0.9:
            for camera_id, reader in self.pipeline.stream_readers.items():
                current_skip = reader.frame_skip
                new_skip = min(current_skip + 1, 5)
                
                if new_skip != current_skip:
                    reader.frame_skip = new_skip
                    self.logger.info(f"Increased frame skip for {camera_id}: {current_skip} → {new_skip}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        if not self._metrics_history:
            return {"error": "No metrics available"}
        
        recent = self._metrics_history[-20:]
        
        return {
            "avg_cpu_percent": np.mean([m.cpu_percent for m in recent]),
            "avg_memory_mb": np.mean([m.memory_mb for m in recent]),
            "avg_processing_time_ms": np.mean([m.processing_time_ms for m in recent])
        }