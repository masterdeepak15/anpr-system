#!/usr/bin/env python3
"""
ANPR System - Main Application Entry Point

Production-grade Automatic Number Plate Recognition System
CPU-only, Real-time, Multi-camera support
"""

import logging
import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.logger import setup_logging
from src.utils.cpu_optimizer import CPUOptimizer
from src.utils.config_loader import ConfigLoader
from src.storage.config_manager import ConfigManager
from src.pipeline.pipeline_controller import PipelineController
from src.api.server import ANPRAPIServer
from src.monitoring.health_monitor import HealthMonitor
from src.supervision.process_supervisor import ProcessSupervisor

def print_banner():
    """Print application banner"""
    banner = """
╔════════════════════════════════════════════════════════════════╗
║                                                                 ║
║              ANPR System - Version 1.0.0                       ║
║         Automatic Number Plate Recognition System              ║
║                                                                 ║
║              Production-Ready | CPU-Only | Real-Time           ║
║                                                                 ║
╚════════════════════════════════════════════════════════════════╝
    """
    print(banner)


class ANPRApplication:
    """
    Main ANPR application class
    
    Integrates all components and manages lifecycle
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize application
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.logger = logging.getLogger("ANPRApplication")
        
        # Components
        self.config_manager = None
        self.pipeline = None
        self.api_server = None
        self.health_monitor = None
        self.supervisor = None
    
    def initialize(self) -> bool:
        """Initialize all application components"""
        try:
            self.logger.info("Initializing ANPR application...")
            
            # Apply CPU optimizations
            CPUOptimizer.optimize_all()
            
            # Load configuration
            config_loader = ConfigLoader(self.config_path)
            config = config_loader.load()
            config = config_loader.merge_with_env(config)
            
            # Initialize config manager (database)
            db_path = config.get('db_path', 'data/anpr_system.db')
            self.config_manager = ConfigManager(db_path=db_path)
            
            # Store config in database
            for key, value in config.items():
                self.config_manager.set_config(key, value)
            
            # Initialize pipeline
            num_workers = config.get('max_workers', CPUOptimizer.get_optimal_workers())
            self.pipeline = PipelineController(
                config_manager=self.config_manager,
                num_workers=num_workers,
                enable_tracking=config.get('enable_tracking', True),
                enable_incident_detection=config.get('enable_incident_detection', True)
            )
            
            if not self.pipeline.initialize():
                self.logger.error("Pipeline initialization failed")
                return False
            
            # Initialize API server
            self.api_server = ANPRAPIServer(
                pipeline_controller=self.pipeline,
                config_manager=self.config_manager,
                host=config.get('api_host', '0.0.0.0'),
                port=config.get('api_port', 5000)
            )
            
            # Link pipeline to API
            self.pipeline.set_api_server(self.api_server)
            
            # Initialize health monitor
            self.health_monitor = HealthMonitor(
                pipeline=self.pipeline,
                check_interval=30
            )
            
            # Initialize supervisor
            self.supervisor = ProcessSupervisor(
                pipeline=self.pipeline,
                max_restarts=5,
                restart_window=300
            )
            
            self.logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}", exc_info=True)
            return False
    
    def start(self) -> None:
        """Start the application"""
        try:
            self.logger.info("Starting ANPR application...")
            
            # Start pipeline
            self.pipeline.start()
            
            # Start health monitoring
            self.health_monitor.start()
            
            # Start supervisor
            self.supervisor.start()
            
            self.logger.info("ANPR System started successfully")
            self.logger.info(f"Processing {len(self.pipeline.stream_readers)} camera(s)")
            self.logger.info(f"API server running on {self.api_server.host}:{self.api_server.port}")
            self.logger.info("Press Ctrl+C to stop")
            
            # Start API server (blocking)
            self.api_server.run(debug=False)
            
        except KeyboardInterrupt:
            self.logger.info("\n Received interrupt signal")
            self.stop()
        except Exception as e:
            self.logger.error(f"Application error: {e}", exc_info=True)
            self.stop()
    
    def stop(self) -> None:
        """Stop the application gracefully"""
        self.logger.info("Stopping ANPR application...")
        
        # Stop in reverse order
        if self.supervisor:
            self.supervisor.stop()
        
        if self.health_monitor:
            self.health_monitor.stop()
        
        if self.pipeline:
            self.pipeline.stop()
        
        self.logger.info("Application stopped successfully")


def main():
    """Main entry point"""
    
    print_banner()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="ANPR System - License Plate Recognition",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default='logs/anpr.log',
        help='Log file path (default: logs/anpr.log)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='ANPR System 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(
        log_level=args.log_level,
        log_file=args.log_file
    )
    
    logger = logging.getLogger("main")
    
    logger.info("=" * 70)
    logger.info("ANPR System Starting")
    logger.info("=" * 70)
    logger.info(f"Configuration file: {args.config}")
    logger.info(f"Log level: {args.log_level}")
    logger.info(f"Log file: {args.log_file}")
    logger.info("=" * 70)
    
    # Create and run application
    app = ANPRApplication(config_path=args.config)
    
    if not app.initialize():
        logger.error("Application initialization failed")
        sys.exit(1)
    
    # Run application
    app.start()
    
    logger.info("ANPR System shutdown complete")


if __name__ == "__main__":
    main()