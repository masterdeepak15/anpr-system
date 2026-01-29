"""Pipeline control API routes"""

from flask import jsonify
import time

def create_pipeline_routes(app, pipeline):
    """Create pipeline control routes"""
    
    @app.route('/api/v1/pipeline/start', methods=['POST'])
    def start_pipeline():
        """Start the processing pipeline"""
        if pipeline._running:
            return jsonify({"message": "Pipeline already running"}), 200
        
        pipeline.start()
        return jsonify({"message": "Pipeline started"})
    
    @app.route('/api/v1/pipeline/stop', methods=['POST'])
    def stop_pipeline():
        """Stop the processing pipeline"""
        if not pipeline._running:
            return jsonify({"message": "Pipeline not running"}), 200
        
        pipeline.stop()
        return jsonify({"message": "Pipeline stopped"})
    
    @app.route('/api/v1/pipeline/restart', methods=['POST'])
    def restart_pipeline():
        """Restart the processing pipeline"""
        if pipeline._running:
            pipeline.stop()
            time.sleep(2)
        
        pipeline.start()
        return jsonify({"message": "Pipeline restarted"})
    
    @app.route('/api/v1/pipeline/stats', methods=['GET'])
    def get_pipeline_stats():
        """Get pipeline statistics"""
        stats = pipeline.get_stats()
        return jsonify(stats)