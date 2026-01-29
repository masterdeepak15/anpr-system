"""Model loading utilities"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import json

try:
    import onnxruntime as ort
except ImportError:
    ort = None

logger = logging.getLogger("ModelLoader")

def load_onnx_model(
    model_path: str,
    num_threads: int = 4,
    optimization_level: str = "all"
) -> Optional[Any]:
    """
    Load ONNX model with optimal settings
    
    Args:
        model_path: Path to ONNX model file
        num_threads: Number of intra-op threads
        optimization_level: "all", "basic", or "extended"
        
    Returns:
        ONNX InferenceSession or None
    """
    if ort is None:
        logger.error("ONNX Runtime not installed")
        return None
    
    if not os.path.exists(model_path):
        logger.error(f"Model not found: {model_path}")
        return None
    
    try:
        # Session options
        sess_options = ort.SessionOptions()
        
        # Set optimization level
        if optimization_level == "all":
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        elif optimization_level == "extended":
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
        else:
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
        
        # Set threading
        sess_options.intra_op_num_threads = num_threads
        sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        
        # Create session
        session = ort.InferenceSession(
            model_path,
            sess_options=sess_options,
            providers=['CPUExecutionProvider']
        )
        
        logger.info(f"Model loaded: {model_path}")
        
        return session
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None


def get_model_info(model_path: str) -> Dict[str, Any]:
    """
    Get information about an ONNX model
    
    Args:
        model_path: Path to model file
        
    Returns:
        Dict with model information
    """
    if ort is None:
        return {"error": "ONNX Runtime not installed"}
    
    try:
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        
        # Get input info
        inputs = []
        for inp in session.get_inputs():
            inputs.append({
                "name": inp.name,
                "shape": inp.shape,
                "type": inp.type
            })
        
        # Get output info
        outputs = []
        for out in session.get_outputs():
            outputs.append({
                "name": out.name,
                "shape": out.shape,
                "type": out.type
            })
        
        return {
            "model_path": model_path,
            "inputs": inputs,
            "outputs": outputs,
            "providers": session.get_providers()
        }
        
    except Exception as e:
        return {"error": str(e)}


def validate_model(model_path: str) -> bool:
    """
    Validate that a model can be loaded
    
    Args:
        model_path: Path to model file
        
    Returns:
        bool: True if valid
    """
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        return False
    
    if ort is None:
        logger.error("ONNX Runtime not installed")
        return False
    
    try:
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        logger.info(f"Model validation successful: {model_path}")
        return True
    except Exception as e:
        logger.error(f"Model validation failed: {e}")
        return False


def save_model_metadata(model_path: str, metadata: Dict[str, Any]) -> bool:
    """
    Save model metadata to JSON file
    
    Args:
        model_path: Path to model file
        metadata: Metadata dictionary
        
    Returns:
        bool: True if successful
    """
    try:
        model_dir = Path(model_path).parent
        metadata_path = model_dir / f"{Path(model_path).stem}_metadata.json"
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved: {metadata_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save metadata: {e}")
        return False


def load_model_metadata(model_path: str) -> Optional[Dict[str, Any]]:
    """
    Load model metadata from JSON file
    
    Args:
        model_path: Path to model file
        
    Returns:
        Dict with metadata or None
    """
    try:
        model_dir = Path(model_path).parent
        metadata_path = model_dir / f"{Path(model_path).stem}_metadata.json"
        
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to load metadata: {e}")
        return None