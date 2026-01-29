"""Multi-frame result aggregation with temporal voting"""

from collections import defaultdict
from typing import List, Dict, Optional
import time
import threading
import logging

from ..core.result import PlateResult

class ResultAggregator:
    """
    Aggregate results across multiple frames using temporal voting
    
    Implements:
    - Sliding window approach
    - Weighted voting based on confidence
    - Duplicate detection
    - Result stabilization
    """
    
    def __init__(
        self,
        window_size: int = 5,
        min_occurrences: int = 3,
        similarity_threshold: float = 0.8,
        result_ttl: int = 30  # seconds
    ):
        """
        Initialize result aggregator
        
        Args:
            window_size: Number of frames to consider
            min_occurrences: Minimum occurrences for consensus
            similarity_threshold: String similarity threshold
            result_ttl: Time-to-live for finalized results (seconds)
        """
        self.window_size = window_size
        self.min_occurrences = min_occurrences
        self.similarity_threshold = similarity_threshold
        self.result_ttl = result_ttl
        
        # Store results per camera
        self._camera_buffers: Dict[str, List[PlateResult]] = defaultdict(list)
        self._finalized_results: Dict[str, List[PlateResult]] = defaultdict(list)
        self._lock = threading.Lock()
        
        self.logger = logging.getLogger("ResultAggregator")
    
    def add_result(self, result: PlateResult) -> Optional[PlateResult]:
        """
        Add a new result and check if we have enough evidence to finalize
        
        Args:
            result: New plate result
            
        Returns:
            Optional[PlateResult]: Finalized result if threshold met, None otherwise
        """
        with self._lock:
            camera_id = result.camera_id
            
            # Add to buffer
            self._camera_buffers[camera_id].append(result)
            
            # Maintain window size
            if len(self._camera_buffers[camera_id]) > self.window_size:
                self._camera_buffers[camera_id].pop(0)
            
            # Clean old finalized results
            self._cleanup_old_results(camera_id)
            
            # Check if we can finalize a result
            finalized = self._try_finalize(camera_id)
            
            if finalized:
                # Check for duplicates
                if not self._is_duplicate(finalized, camera_id):
                    self._finalized_results[camera_id].append(finalized)
                    self.logger.info(
                        f"Finalized result: {finalized.plate_text} "
                        f"(confidence: {finalized.confidence:.2f})"
                    )
                    return finalized
            
            return None
    
    def _try_finalize(self, camera_id: str) -> Optional[PlateResult]:
        """
        Attempt to finalize a result using voting logic
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Optional[PlateResult]: Consensus result or None
        """
        buffer = self._camera_buffers[camera_id]
        
        if len(buffer) < self.min_occurrences:
            return None
        
        # Group similar plates
        plate_groups = defaultdict(list)
        
        for result in buffer:
            # Find matching group
            matched = False
            for plate_text in plate_groups.keys():
                if self._are_similar(plate_text, result.plate_text):
                    plate_groups[plate_text].append(result)
                    matched = True
                    break
            
            if not matched:
                plate_groups[result.plate_text].append(result)
        
        # Find group with most occurrences
        best_group = None
        best_count = 0
        
        for plate_text, results in plate_groups.items():
            if len(results) > best_count:
                best_count = len(results)
                best_group = results
        
        # Check if we have enough evidence
        if best_count >= self.min_occurrences:
            # Create consensus result
            return self._create_consensus(best_group)
        
        return None
    
    def _are_similar(self, text1: str, text2: str) -> bool:
        """
        Check if two plate texts are similar using Levenshtein-like logic
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            bool: True if similar
        """
        if text1 == text2:
            return True
        
        # Quick reject if length difference too large
        if abs(len(text1) - len(text2)) > 1:
            return False
        
        # Calculate character differences
        max_len = max(len(text1), len(text2))
        differences = sum(
            c1 != c2 for c1, c2 in zip(text1.ljust(max_len), text2.ljust(max_len))
        )
        
        similarity = 1.0 - (differences / max_len)
        
        return similarity >= self.similarity_threshold
    
    def _create_consensus(self, results: List[PlateResult]) -> PlateResult:
        """
        Create a consensus result from multiple detections
        
        Args:
            results: List of similar results
            
        Returns:
            PlateResult: Consensus result
        """
        # Use the result with highest confidence as base
        best_result = max(results, key=lambda r: r.confidence)
        
        # Calculate weighted average confidence
        total_weight = sum(r.confidence for r in results)
        weighted_conf = sum(r.confidence * r.confidence for r in results) / total_weight
        
        # Collect all raw detections
        raw_detections = [r.plate_text for r in results]
        
        # Merge character confidences (average per position)
        merged_char_conf = []
        if best_result.character_confidences:
            num_chars = len(best_result.character_confidences)
            for i in range(num_chars):
                char_confs = [
                    r.character_confidences[i] 
                    for r in results 
                    if i < len(r.character_confidences)
                ]
                merged_char_conf.append(
                    sum(char_confs) / len(char_confs) if char_confs else 0.0
                )
        
        # Create consensus result
        return PlateResult(
            plate_text=best_result.plate_text,
            confidence=float(weighted_conf),
            bbox=best_result.bbox,
            frame_id=best_result.frame_id,
            camera_id=best_result.camera_id,
            timestamp=best_result.timestamp,
            character_confidences=merged_char_conf,
            raw_detections=raw_detections
        )
    
    def _is_duplicate(self, result: PlateResult, camera_id: str) -> bool:
        """
        Check if this result is a duplicate of a recent finalized result
        
        Args:
            result: New result
            camera_id: Camera identifier
            
        Returns:
            bool: True if duplicate
        """
        finalized = self._finalized_results[camera_id]
        
        for past_result in finalized:
            # Same plate within time window
            if (self._are_similar(result.plate_text, past_result.plate_text) and
                abs(result.timestamp - past_result.timestamp) < self.result_ttl):
                self.logger.debug(
                    f"Duplicate detected: {result.plate_text} "
                    f"(last seen {result.timestamp - past_result.timestamp:.1f}s ago)"
                )
                return True
        
        return False
    
    def _cleanup_old_results(self, camera_id: str) -> None:
        """
        Remove results older than TTL
        
        Args:
            camera_id: Camera identifier
        """
        current_time = time.time()
        
        self._finalized_results[camera_id] = [
            r for r in self._finalized_results[camera_id]
            if current_time - r.timestamp < self.result_ttl
        ]
    
    def get_stats(self, camera_id: str) -> Dict[str, any]:
        """
        Get aggregator statistics for a camera
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Dict: Statistics
        """
        with self._lock:
            return {
                "camera_id": camera_id,
                "buffer_size": len(self._camera_buffers[camera_id]),
                "finalized_count": len(self._finalized_results[camera_id]),
                "window_size": self.window_size,
                "min_occurrences": self.min_occurrences
            }
    
    def clear_camera(self, camera_id: str) -> None:
        """
        Clear all data for a camera
        
        Args:
            camera_id: Camera identifier
        """
        with self._lock:
            self._camera_buffers[camera_id].clear()
            self._finalized_results[camera_id].clear()
            self.logger.info(f"Cleared data for camera: {camera_id}")
    
    def __repr__(self) -> str:
        return (f"ResultAggregator(window={self.window_size}, "
                f"min_occur={self.min_occurrences})")