"""Flask API server for ANPR system"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import time
from queue import Queue, Empty
from typing import Generator, Dict, Any
import threading
import logging

class ANPRAPIServer:
    """
    Flask-based REST API and SSE server
    
    Endpoints:
    - REST: Camera management, results query, system stats
    - SSE: Real-time plate detection events
    """
    
    def __init__(
        self,
        pipeline_controller,
        config_manager,
        host: str = "0.0.0.0",
        port: int = 5000
    ):
        """
        Initialize API server
        
        Args:
            pipeline_controller: Pipeline controller instance
            config_manager: Configuration manager instance
            host: Server host
            port: Server port
        """
        self.pipeline = pipeline_controller
        self.config = config_manager
        self.host = host
        self.port = port
        
        # Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # SSE subscribers
        self._sse_subscribers: Dict[str, Queue] = {}
        self._sse_lock = threading.Lock()
        
        self.logger = logging.getLogger("APIServer")
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self) -> None:
        """Register all API routes"""
        
        # Health check
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                "status": "healthy",
                "timestamp": time.time()
            })
        
        # System status
        @self.app.route('/api/v1/status', methods=['GET'])
        def get_status():
            stats = self.pipeline.get_stats()
            return jsonify({
                "status": "running" if self.pipeline._running else "stopped",
                "stats": stats
            })
        
        # Camera routes
        from .routes.cameras import create_camera_routes
        create_camera_routes(self.app, self.config, self.pipeline)
        
        # Results routes
        from .routes.results import create_result_routes
        create_result_routes(self.app, self.config)
        
        # Config routes
        from .routes.config import create_config_routes
        create_config_routes(self.app, self.config)
        
        # Pipeline routes
        from .routes.pipeline import create_pipeline_routes
        create_pipeline_routes(self.app, self.pipeline)
        
        # Events (SSE)
        from .routes.events import create_event_routes
        create_event_routes(self.app, self)

        # Image detection route
        from .routes.image_detection import create_image_detection_route
        create_image_detection_route(self.app, self.pipeline)

        # Incident routes
        from .routes.incidents import create_incident_routes
        create_incident_routes(self.app, self.config, self.pipeline)
    
    def broadcast_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast event to all SSE subscribers"""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "data": data
        }
        
        with self._sse_lock:
            for queue in self._sse_subscribers.values():
                try:
                    queue.put_nowait(event)
                except:
                    pass
    
    def run(self, debug: bool = False) -> None:
        """Run the Flask server"""
        self.logger.info(f"Starting API server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug, threaded=True)