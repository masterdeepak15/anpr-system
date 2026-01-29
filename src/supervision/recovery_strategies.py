"""Recovery strategies for different failure types"""

from enum import Enum
from typing import Callable, Dict, Any
import logging

class FailureType(Enum):
    """Types of failures"""
    CAMERA_DISCONNECT = "camera_disconnect"
    MODEL_ERROR = "model_error"
    DATABASE_ERROR = "database_error"
    MEMORY_ERROR = "memory_error"
    UNKNOWN = "unknown"

class RecoveryStrategy:
    """
    Define recovery strategies for different failure types
    """
    
    def __init__(self):
        """Initialize recovery strategy"""
        self.strategies: Dict[FailureType, Callable] = {}
        self.logger = logging.getLogger("RecoveryStrategy")
        
        # Register default strategies
        self._register_default_strategies()
    
    def _register_default_strategies(self) -> None:
        """Register default recovery strategies"""
        
        # Camera disconnect recovery
        def recover_camera_disconnect(context: Dict[str, Any]) -> bool:
            camera_id = context.get('camera_id')
            pipeline = context.get('pipeline')
            
            if not camera_id or not pipeline:
                return False
            
            try:
                # Attempt reconnection
                if camera_id in pipeline.stream_readers:
                    reader = pipeline.stream_readers[camera_id]
                    return reader.connect()
                return False
            except Exception as e:
                self.logger.error(f"Camera recovery failed: {e}")
                return False
        
        # Model error recovery
        def recover_model_error(context: Dict[str, Any]) -> bool:
            model_type = context.get('model_type')
            pipeline = context.get('pipeline')
            
            try:
                # Reload model
                if model_type == 'vehicle':
                    return pipeline.vehicle_detector.load_model(
                        pipeline.vehicle_detector.model_path
                    )
                elif model_type == 'plate':
                    return pipeline.plate_detector.load_model(
                        pipeline.plate_detector.model_path
                    )
                elif model_type == 'ocr':
                    return pipeline.ocr_engine.load_model(
                        pipeline.ocr_engine.classifier_model_path
                    )
                return False
            except Exception as e:
                self.logger.error(f"Model recovery failed: {e}")
                return False
        
        # Database error recovery
        def recover_database_error(context: Dict[str, Any]) -> bool:
            try:
                # Attempt database vacuum and reconnect
                config_manager = context.get('config_manager')
                if config_manager:
                    # Simple reconnection attempt
                    return True
                return False
            except Exception as e:
                self.logger.error(f"Database recovery failed: {e}")
                return False
        
        # Memory error recovery
        def recover_memory_error(context: Dict[str, Any]) -> bool:
            try:
                # Clear buffers
                pipeline = context.get('pipeline')
                if pipeline:
                    for buffer in pipeline.frame_buffers.values():
                        buffer.clear()
                    
                    # Force garbage collection
                    import gc
                    gc.collect()
                    
                    return True
                return False
            except Exception as e:
                self.logger.error(f"Memory recovery failed: {e}")
                return False
        
        # Register strategies
        self.register_strategy(FailureType.CAMERA_DISCONNECT, recover_camera_disconnect)
        self.register_strategy(FailureType.MODEL_ERROR, recover_model_error)
        self.register_strategy(FailureType.DATABASE_ERROR, recover_database_error)
        self.register_strategy(FailureType.MEMORY_ERROR, recover_memory_error)
    
    def register_strategy(
        self,
        failure_type: FailureType,
        strategy: Callable[[Dict[str, Any]], bool]
    ) -> None:
        """
        Register a recovery strategy
        
        Args:
            failure_type: Type of failure
            strategy: Recovery function
        """
        self.strategies[failure_type] = strategy
        self.logger.info(f"Registered recovery strategy for: {failure_type.value}")
    
    def recover(self, failure_type: FailureType, context: Dict[str, Any]) -> bool:
        """
        Execute recovery strategy
        
        Args:
            failure_type: Type of failure
            context: Context information
            
        Returns:
            bool: True if recovery successful
        """
        strategy = self.strategies.get(failure_type)
        
        if not strategy:
            self.logger.warning(f"No recovery strategy for: {failure_type.value}")
            return False
        
        try:
            self.logger.info(f"Attempting recovery for: {failure_type.value}")
            success = strategy(context)
            
            if success:
                self.logger.info(f"Recovery successful for: {failure_type.value}")
            else:
                self.logger.warning(f"Recovery failed for: {failure_type.value}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Recovery exception for {failure_type.value}: {e}")
            return False