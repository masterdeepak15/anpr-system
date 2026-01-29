"""Character classification using ML model"""

import cv2
import numpy as np
from typing import Tuple, Optional, Dict, List
import logging

try:
    import onnxruntime as ort
except ImportError:
    ort = None

class CharacterClassifier:
    """
    Classify individual character images
    
    Uses pre-trained ONNX model for classification
    """
    
    def __init__(
        self,
        model_path: str,
        input_size: Tuple[int, int] = (28, 28)
    ):
        """
        Initialize classifier
        
        Args:
            model_path: Path to ONNX model
            input_size: Model input size (width, height)
        """
        self.model_path = model_path
        self.input_size = input_size
        
        self._session: Optional[ort.InferenceSession] = None
        self._char_dict = self._build_char_dictionary()
        
        self.logger = logging.getLogger("CharacterClassifier")
        
        # Load model
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str) -> bool:
        """Load character classification model"""
        if ort is None:
            self.logger.error("ONNX Runtime not installed")
            return False
        
        try:
            self.logger.info(f"Loading character classifier: {model_path}")
            
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.intra_op_num_threads = 2
            
            self._session = ort.InferenceSession(
                model_path,
                sess_options=sess_options,
                providers=['CPUExecutionProvider']
            )
            
            self.logger.info("Character classifier loaded")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False
    
    def classify(self, char_image: np.ndarray) -> Tuple[str, float]:
        """
        Classify a single character
        
        Args:
            char_image: Character image (grayscale)
            
        Returns:
            Tuple of (character, confidence)
        """
        if self._session is None:
            self.logger.warning("Model not loaded")
            return ("?", 0.0)
        
        try:
            # Preprocess
            input_tensor = self._preprocess(char_image)
            
            # Run inference
            input_name = self._session.get_inputs()[0].name
            output_name = self._session.get_outputs()[0].name
            
            result = self._session.run(
                [output_name],
                {input_name: input_tensor}
            )[0]
            
            # Get predicted class
            class_id = np.argmax(result)
            confidence = float(result[0][class_id])
            
            # Map class ID to character
            character = self._char_dict.get(class_id, "?")
            
            return (character, confidence)
            
        except Exception as e:
            self.logger.error(f"Classification failed: {e}")
            return ("?", 0.0)
    
    def _preprocess(self, char_image: np.ndarray) -> np.ndarray:
        """
        Preprocess character image for model
        
        Args:
            char_image: Input character image
            
        Returns:
            np.ndarray: Preprocessed tensor
        """
        # Resize to model input size
        resized = cv2.resize(char_image, self.input_size)
        
        # Normalize to [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # Reshape for model: (1, 1, height, width)
        input_tensor = normalized.reshape(1, 1, self.input_size[1], self.input_size[0])
        
        return input_tensor
    
    def _build_char_dictionary(self) -> Dict[int, str]:
        """
        Build character dictionary (class_id -> character)
        
        Returns:
            Dict mapping class IDs to characters
        """
        # Alphanumeric characters
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return {i: char for i, char in enumerate(chars)}
    
    def classify_batch(self, char_images: List[np.ndarray]) -> List[Tuple[str, float]]:
        """
        Classify multiple characters (batch processing)
        
        Args:
            char_images: List of character images
            
        Returns:
            List of (character, confidence) tuples
        """
        results = []
        
        for char_img in char_images:
            result = self.classify(char_img)
            results.append(result)
        
        return results
    
    def __repr__(self) -> str:
        return f"CharacterClassifier(model_loaded={self._session is not None})"