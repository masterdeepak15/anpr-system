"""Consensus building utilities"""

from typing import List, Dict, Tuple
from collections import Counter
import numpy as np

from ..core.result import PlateResult

class ConsensusBuilder:
    """
    Build consensus from multiple OCR results
    
    Provides various consensus strategies
    """
    
    @staticmethod
    def majority_vote(results: List[PlateResult]) -> PlateResult:
        """
        Use majority voting to determine consensus
        
        Args:
            results: List of plate results
            
        Returns:
            PlateResult: Consensus result
        """
        if not results:
            raise ValueError("Cannot build consensus from empty results")
        
        # Count occurrences of each plate text
        plate_counts = Counter(r.plate_text for r in results)
        
        # Get most common
        most_common_text, count = plate_counts.most_common(1)[0]
        
        # Find result with that text and highest confidence
        matching_results = [r for r in results if r.plate_text == most_common_text]
        best_result = max(matching_results, key=lambda r: r.confidence)
        
        return best_result
    
    @staticmethod
    def weighted_vote(results: List[PlateResult]) -> PlateResult:
        """
        Use confidence-weighted voting
        
        Args:
            results: List of plate results
            
        Returns:
            PlateResult: Consensus result
        """
        if not results:
            raise ValueError("Cannot build consensus from empty results")
        
        # Group by plate text and sum confidences
        plate_weights: Dict[str, float] = {}
        plate_results: Dict[str, List[PlateResult]] = {}
        
        for result in results:
            text = result.plate_text
            if text not in plate_weights:
                plate_weights[text] = 0.0
                plate_results[text] = []
            
            plate_weights[text] += result.confidence
            plate_results[text].append(result)
        
        # Find text with highest total weight
        best_text = max(plate_weights.items(), key=lambda x: x[1])[0]
        
        # Return highest confidence result with that text
        return max(plate_results[best_text], key=lambda r: r.confidence)
    
    @staticmethod
    def character_level_vote(results: List[PlateResult]) -> Tuple[str, List[float]]:
        """
        Build consensus at character level
        
        Args:
            results: List of plate results
            
        Returns:
            Tuple: (consensus_text, character_confidences)
        """
        if not results:
            raise ValueError("Cannot build consensus from empty results")
        
        # Find maximum length
        max_len = max(len(r.plate_text) for r in results)
        
        # Vote on each character position
        consensus_text = []
        char_confidences = []
        
        for pos in range(max_len):
            # Collect characters at this position
            chars_at_pos = []
            confs_at_pos = []
            
            for result in results:
                if pos < len(result.plate_text):
                    chars_at_pos.append(result.plate_text[pos])
                    
                    # Get confidence for this character
                    if pos < len(result.character_confidences):
                        confs_at_pos.append(result.character_confidences[pos])
                    else:
                        confs_at_pos.append(result.confidence)
            
            if not chars_at_pos:
                continue
            
            # Weighted vote for this position
            char_weights: Dict[str, float] = {}
            for char, conf in zip(chars_at_pos, confs_at_pos):
                if char not in char_weights:
                    char_weights[char] = 0.0
                char_weights[char] += conf
            
            # Select character with highest weight
            best_char = max(char_weights.items(), key=lambda x: x[1])[0]
            consensus_text.append(best_char)
            
            # Average confidence for this position
            avg_conf = np.mean(confs_at_pos) if confs_at_pos else 0.0
            char_confidences.append(float(avg_conf))
        
        return ("".join(consensus_text), char_confidences)
    
    @staticmethod
    def best_confidence(results: List[PlateResult]) -> PlateResult:
        """
        Simply return result with highest confidence
        
        Args:
            results: List of plate results
            
        Returns:
            PlateResult: Result with highest confidence
        """
        if not results:
            raise ValueError("Cannot build consensus from empty results")
        
        return max(results, key=lambda r: r.confidence)
    
    @staticmethod
    def average_result(results: List[PlateResult]) -> PlateResult:
        """
        Create averaged result (for identical plates)
        
        Args:
            results: List of identical plate results
            
        Returns:
            PlateResult: Averaged result
        """
        if not results:
            raise ValueError("Cannot build consensus from empty results")
        
        # All should have same text
        plate_text = results[0].plate_text
        
        # Average confidence
        avg_confidence = float(np.mean([r.confidence for r in results]))
        
        # Use first result as template
        template = results[0]
        
        return PlateResult(
            plate_text=plate_text,
            confidence=avg_confidence,
            bbox=template.bbox,
            frame_id=template.frame_id,
            camera_id=template.camera_id,
            timestamp=template.timestamp,
            character_confidences=template.character_confidences,
            raw_detections=[r.plate_text for r in results]
        )