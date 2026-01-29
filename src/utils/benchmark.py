"""Performance benchmarking utilities"""

import time
import numpy as np
from typing import Dict, Any, Callable
import logging

class PerformanceBenchmark:
    """
    Benchmark system performance
    """
    
    @staticmethod
    def benchmark_function(
        func: Callable,
        *args,
        iterations: int = 100,
        **kwargs
    ) -> Dict[str, float]:
        """
        Benchmark a function
        
        Args:
            func: Function to benchmark
            iterations: Number of iterations
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Dict: Benchmark results
        """
        times = []
        
        for _ in range(iterations):
            start = time.time()
            func(*args, **kwargs)
            elapsed = (time.time() - start) * 1000  # ms
            times.append(elapsed)
        
        return {
            "avg_ms": np.mean(times),
            "min_ms": np.min(times),
            "max_ms": np.max(times),
            "std_ms": np.std(times),
            "median_ms": np.median(times),
            "fps": 1000 / np.mean(times)
        }
    
    @staticmethod
    def benchmark_detector(
        detector,
        test_image: np.ndarray,
        iterations: int = 100
    ) -> Dict[str, float]:
        """
        Benchmark detection speed
        
        Args:
            detector: Detector instance
            test_image: Test image
            iterations: Number of iterations
            
        Returns:
            Dict: Benchmark results
        """
        return PerformanceBenchmark.benchmark_function(
            detector.detect,
            test_image,
            iterations=iterations
        )
    
    @staticmethod
    def estimate_capacity(
        single_frame_time_ms: float,
        num_cameras: int,
        target_fps: float = 5.0
    ) -> Dict[str, Any]:
        """
        Estimate system capacity
        
        Args:
            single_frame_time_ms: Time to process one frame
            num_cameras: Number of cameras
            target_fps: Target FPS per camera
            
        Returns:
            Dict: Capacity estimation
        """
        # Time budget per second
        time_budget_ms = 1000.0
        
        # Time required per camera per second
        time_per_camera_ms = target_fps * single_frame_time_ms
        
        # Total time required
        total_time_ms = num_cameras * time_per_camera_ms
        
        # CPU utilization
        cpu_utilization = (total_time_ms / time_budget_ms) * 100
        
        # Max cameras at target FPS
        max_cameras = int(time_budget_ms / time_per_camera_ms) if time_per_camera_ms > 0 else 0
        
        return {
            "target_fps": target_fps,
            "num_cameras": num_cameras,
            "single_frame_time_ms": single_frame_time_ms,
            "estimated_cpu_utilization": cpu_utilization,
            "max_cameras_at_target_fps": max_cameras,
            "feasible": cpu_utilization < 80
        }
    
    @staticmethod
    def generate_report(results: Dict[str, float]) -> str:
        """
        Generate benchmark report
        
        Args:
            results: Benchmark results
            
        Returns:
            str: Formatted report
        """
        report = "Performance Benchmark Report\n"
        report += "=" * 50 + "\n"
        report += f"Average Time: {results['avg_ms']:.2f}ms\n"
        report += f"Minimum Time: {results['min_ms']:.2f}ms\n"
        report += f"Maximum Time: {results['max_ms']:.2f}ms\n"
        report += f"Std Deviation: {results['std_ms']:.2f}ms\n"
        report += f"Median Time: {results['median_ms']:.2f}ms\n"
        report += f"Throughput: {results['fps']:.2f} FPS\n"
        report += "=" * 50 + "\n"
        
        return report