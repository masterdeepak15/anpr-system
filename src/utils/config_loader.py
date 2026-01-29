"""Configuration loading utilities"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

class ConfigLoader:
    """
    Load configuration from JSON files
    
    Supports environment-specific configs
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize config loader
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.logger = logging.getLogger("ConfigLoader")
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file
        
        Returns:
            Dict: Configuration data
        """
        try:
            if not os.path.exists(self.config_path):
                self.logger.warning(f"Config file not found: {self.config_path}")
                return self._get_default_config()
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            self.logger.info(f"Configuration loaded from: {self.config_path}")
            return config
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
            return self._get_default_config()
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def save(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to file
        
        Args:
            config: Configuration data
            
        Returns:
            bool: True if successful
        """
        try:
            # Ensure directory exists
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Configuration saved to: {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False
    
    def merge_with_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge config with environment variables
        
        Environment variables override config file values
        
        Args:
            config: Base configuration
            
        Returns:
            Dict: Merged configuration
        """
        env_mappings = {
            'API_HOST': 'api_host',
            'API_PORT': 'api_port',
            'LOG_LEVEL': 'log_level',
            'DB_PATH': 'db_path',
            'MAX_WORKERS': 'max_workers'
        }
        
        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value:
                # Type conversion
                if config_key == 'api_port' or config_key == 'max_workers':
                    env_value = int(env_value)
                
                config[config_key] = env_value
                self.logger.debug(f"Config override from env: {config_key}={env_value}")
        
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "frame_width": 640,
            "frame_height": 480,
            "vehicle_model_path": "models/vehicle_detector.onnx",
            "plate_model_path": "models/plate_detector.onnx",
            "ocr_model_path": "models/char_classifier.onnx",
            "country_code": "IN",
            "api_host": "0.0.0.0",
            "api_port": 5000,
            "target_fps": 5.0,
            "max_cpu_percent": 80.0
        }
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            bool: True if valid
        """
        required_keys = [
            'vehicle_model_path',
            'plate_model_path',
            'ocr_model_path',
            'country_code'
        ]
        
        for key in required_keys:
            if key not in config:
                self.logger.error(f"Missing required config key: {key}")
                return False
        
        return True