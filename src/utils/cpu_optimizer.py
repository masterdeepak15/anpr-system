"""CPU optimization utilities"""

import cv2
import os
import multiprocessing
import logging

class CPUOptimizer:
    """
    CPU optimization utilities
    
    Provides methods to optimize CPU-only processing
    """
    
    @staticmethod
    def optimize_opencv() -> None:
        """Optimize OpenCV for CPU processing"""
        try:
            # Set number of threads
            cv2.setNumThreads(4)
            
            # Use optimized code paths
            cv2.setUseOptimized(True)
            
            # Disable OpenCL (we're CPU-only)
            cv2.ocl.setUseOpenCL(False)
            
            logging.info("OpenCV optimized for CPU")
        except Exception as e:
            logging.warning(f"OpenCV optimization failed: {e}")
    
    @staticmethod
    def optimize_numpy() -> None:
        """Optimize NumPy operations"""
        try:
            # Set number of threads for NumPy operations
            os.environ['OMP_NUM_THREADS'] = '4'
            os.environ['OPENBLAS_NUM_THREADS'] = '4'
            os.environ['MKL_NUM_THREADS'] = '4'
            os.environ['NUMEXPR_NUM_THREADS'] = '4'
            
            logging.info("NumPy optimized for CPU")
        except Exception as e:
            logging.warning(f"NumPy optimization failed: {e}")
    
    @staticmethod
    def set_process_priority(priority: str = "high") -> None:
        """
        Set process priority (Unix/Linux)
        
        Args:
            priority: "high", "normal", or "low"
        """
        try:
            import os
            if priority == "high":
                os.nice(-10)  # Higher priority
            elif priority == "low":
                os.nice(10)   # Lower priority
            # normal = default, no change
            
            logging.info(f"Process priority set to: {priority}")
        except Exception as e:
            logging.warning(f"Failed to set priority: {e}")
    
    @staticmethod
    def get_optimal_workers() -> int:
        """
        Calculate optimal number of workers
        
        Returns:
            int: Optimal worker count
        """
        cpu_count = multiprocessing.cpu_count()
        
        # Leave at least 2 cores for system/capture threads
        optimal = max(2, cpu_count - 2)
        
        return optimal
    
    @staticmethod
    def enable_fast_math() -> None:
        """Enable fast math optimizations"""
        try:
            import numpy as np
            # Ignore floating point errors for speed
            np.seterr(all='ignore')
            
            logging.info("Fast math enabled")
        except Exception as e:
            logging.warning(f"Fast math enable failed: {e}")
    
    @staticmethod
    def optimize_all() -> None:
        """Apply all CPU optimizations"""
        CPUOptimizer.optimize_opencv()
        CPUOptimizer.optimize_numpy()
        CPUOptimizer.enable_fast_math()
        
        logging.info("All CPU optimizations applied")