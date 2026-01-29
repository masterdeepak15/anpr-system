"""Prometheus metrics exporter"""

import logging
from typing import Dict, Any

try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

class MetricsExporter:
    """
    Export metrics to Prometheus
    """
    
    def __init__(self, port: int = 9090):
        """
        Initialize metrics exporter
        
        Args:
            port: Metrics server port
        """
        self.port = port
        self.logger = logging.getLogger("MetricsExporter")
        
        if not PROMETHEUS_AVAILABLE:
            self.logger.warning("Prometheus client not available. Install with: pip install prometheus-client")
            return
        
        # Define metrics
        self.frames_processed = Counter(
            'anpr_frames_processed_total',
            'Total frames processed',
            ['camera_id']
        )
        
        self.plates_detected = Counter(
            'anpr_plates_detected_total',
            'Total plates detected',
            ['camera_id']
        )
        
        self.processing_time = Histogram(
            'anpr_processing_time_seconds',
            'Frame processing time',
            ['camera_id']
        )
        
        self.queue_size = Gauge(
            'anpr_queue_size',
            'Current queue size',
            ['camera_id']
        )
        
        self.cpu_usage = Gauge(
            'anpr_cpu_usage_percent',
            'CPU usage percentage'
        )
        
        self.memory_usage = Gauge(
            'anpr_memory_usage_mb',
            'Memory usage in MB'
        )
        
        self.camera_status = Gauge(
            'anpr_camera_connected',
            'Camera connection status',
            ['camera_id']
        )
    
    def start(self) -> bool:
        """Start metrics server"""
        if not PROMETHEUS_AVAILABLE:
            return False
        
        try:
            start_http_server(self.port)
            self.logger.info(f"Metrics server started on port {self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start metrics server: {e}")
            return False
    
    def update_from_pipeline(self, pipeline) -> None:
        """Update metrics from pipeline stats"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        stats = pipeline.get_stats()
        
        # Update system metrics
        import psutil
        process = psutil.Process()
        self.cpu_usage.set(process.cpu_percent())
        self.memory_usage.set(process.memory_info().rss / 1024 / 1024)