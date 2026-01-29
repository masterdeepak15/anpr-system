"""System health monitoring"""

import threading
import time
import psutil
from typing import Dict, Any, Callable, Optional
import logging

class HealthMonitor:
    """
    Monitor system health
    
    Checks:
    - Process health
    - Camera connectivity
    - Resource usage
    """
    
    def __init__(
        self,
        pipeline,
        check_interval: int = 30,
        alert_callback: Optional[Callable] = None
    ):
        """
        Initialize health monitor
        
        Args:
            pipeline: Pipeline controller
            check_interval: Check interval in seconds
            alert_callback: Callback for alerts
        """
        self.pipeline = pipeline
        self.check_interval = check_interval
        self.alert_callback = alert_callback
        
        self._monitoring = False
        self._monitor_thread = None
        
        self.logger = logging.getLogger("HealthMonitor")
    
    def start(self) -> None:
        """Start health monitoring"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self.logger.info("Health monitoring started")
    
    def stop(self) -> None:
        """Stop health monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self._monitoring:
            try:
                health_status = self._check_health()
                
                if not health_status['healthy']:
                    self._handle_unhealthy(health_status)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
    
    def _check_health(self) -> Dict[str, Any]:
        """Perform health checks"""
        issues = []
        healthy = True
        
        # Check pipeline
        if not self.pipeline._running:
            issues.append("Pipeline not running")
            healthy = False
        
        # Check cameras
        for camera_id, reader in self.pipeline.stream_readers.items():
            if not reader.is_connected():
                issues.append(f"Camera {camera_id} disconnected")
                healthy = False
        
        # Check resources
        process = psutil.Process()
        cpu_percent = process.cpu_percent()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if cpu_percent > 95:
            issues.append(f"Critical CPU usage: {cpu_percent:.1f}%")
            healthy = False
        
        if memory_mb > 3000:
            issues.append(f"High memory usage: {memory_mb:.1f}MB")
            healthy = False
        
        return {
            "healthy": healthy,
            "timestamp": time.time(),
            "issues": issues,
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb
        }
    
    def _handle_unhealthy(self, health_status: Dict[str, Any]) -> None:
        """Handle unhealthy state"""
        self.logger.error(f"System unhealthy: {', '.join(health_status['issues'])}")
        
        if self.alert_callback:
            self.alert_callback(health_status)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return self._check_health()