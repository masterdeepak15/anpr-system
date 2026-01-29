"""Process supervisor for automatic restart on failure"""

import threading
import time
from typing import List
import logging

class ProcessSupervisor:
    """
    Process supervisor for automatic restart
    
    Monitors pipeline and restarts on failure
    """
    
    def __init__(
        self,
        pipeline,
        max_restarts: int = 5,
        restart_window: int = 300  # 5 minutes
    ):
        """
        Initialize supervisor
        
        Args:
            pipeline: Pipeline controller
            max_restarts: Max restart attempts in window
            restart_window: Time window in seconds
        """
        self.pipeline = pipeline
        self.max_restarts = max_restarts
        self.restart_window = restart_window
        
        self._restart_count = 0
        self._restart_times: List[float] = []
        self._supervising = False
        self._supervisor_thread = None
        
        self.logger = logging.getLogger("ProcessSupervisor")
    
    def start(self) -> None:
        """Start supervision"""
        if self._supervising:
            return
        
        self._supervising = True
        self._supervisor_thread = threading.Thread(
            target=self._supervise_loop,
            daemon=True
        )
        self._supervisor_thread.start()
        
        self.logger.info("Process supervision started")
    
    def stop(self) -> None:
        """Stop supervision"""
        self._supervising = False
        if self._supervisor_thread:
            self._supervisor_thread.join(timeout=5)
    
    def _supervise_loop(self) -> None:
        """Main supervision loop"""
        while self._supervising:
            try:
                # Check if pipeline is running
                if not self.pipeline._running:
                    self.logger.warning("Pipeline stopped unexpectedly, attempting restart")
                    self._attempt_restart()
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Supervision error: {e}")
    
    def _attempt_restart(self) -> bool:
        """Attempt to restart the pipeline"""
        current_time = time.time()
        
        # Clean old restart times
        self._restart_times = [
            t for t in self._restart_times
            if current_time - t < self.restart_window
        ]
        
        # Check restart limit
        if len(self._restart_times) >= self.max_restarts:
            self.logger.critical(
                f"Max restart limit reached ({self.max_restarts} in {self.restart_window}s)"
            )
            self._supervising = False
            return False
        
        try:
            self.logger.info("Restarting pipeline...")
            
            # Restart
            self.pipeline.initialize()
            self.pipeline.start()
            
            # Record restart
            self._restart_times.append(current_time)
            self._restart_count += 1
            
            self.logger.info(f"Pipeline restarted (restart count: {self._restart_count})")
            return True
            
        except Exception as e:
            self.logger.error(f"Restart failed: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get supervisor statistics"""
        return {
            "supervising": self._supervising,
            "total_restarts": self._restart_count,
            "recent_restarts": len(self._restart_times),
            "max_restarts": self.max_restarts,
            "restart_window": self.restart_window
        }