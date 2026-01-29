"""Worker pool management utilities"""

import multiprocessing
import psutil
from typing import Dict, Any
import logging

class WorkerManager:
    """
    Manage worker pool size and performance
    
    Dynamically adjusts workers based on load
    """
    
    def __init__(self):
        """Initialize worker manager"""
        self.logger = logging.getLogger("WorkerManager")
    
    @staticmethod
    def get_optimal_workers(cpu_reserved: int = 2) -> int:
        """
        Calculate optimal number of workers
        
        Args:
            cpu_reserved: CPU cores to reserve for system
            
        Returns:
            int: Optimal worker count
        """
        cpu_count = multiprocessing.cpu_count()
        optimal = max(2, cpu_count - cpu_reserved)
        
        return optimal
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """
        Get system resource information
        
        Returns:
            Dict: System information
        """
        cpu_count = multiprocessing.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        memory = psutil.virtual_memory()
        memory_total_gb = memory.total / (1024 ** 3)
        memory_available_gb = memory.available / (1024 ** 3)
        memory_percent = memory.percent
        
        return {
            "cpu_count": cpu_count,
            "cpu_percent": cpu_percent,
            "memory_total_gb": round(memory_total_gb, 2),
            "memory_available_gb": round(memory_available_gb, 2),
            "memory_percent": memory_percent
        }
    
    @staticmethod
    def calculate_max_cameras(
        single_frame_time_ms: float,
        target_fps: float = 5.0,
        cpu_limit_percent: float = 80.0
    ) -> int:
        """
        Calculate maximum cameras for target FPS
        
        Args:
            single_frame_time_ms: Time to process one frame
            target_fps: Target FPS per camera
            cpu_limit_percent: Max CPU utilization
            
        Returns:
            int: Maximum number of cameras
        """
        # Time budget per second (in ms)
        time_budget_ms = 1000.0 * (cpu_limit_percent / 100.0)
        
        # Time required per camera per second
        time_per_camera_ms = target_fps * single_frame_time_ms
        
        # Max cameras
        if time_per_camera_ms > 0:
            max_cameras = int(time_budget_ms / time_per_camera_ms)
            return max(1, max_cameras)
        
        return 1
    
    @staticmethod
    def get_load_recommendation(current_load: float) -> str:
        """
        Get load recommendation
        
        Args:
            current_load: Current CPU load percentage
            
        Returns:
            str: Recommendation
        """
        if current_load < 50:
            return "System has capacity - can add more cameras"
        elif current_load < 70:
            return "System load is optimal"
        elif current_load < 85:
            return "System load is high - consider reducing cameras or frame rate"
        else:
            return "System overloaded - reduce cameras or frame rate immediately"