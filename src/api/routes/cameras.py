"""Camera management API routes"""

from flask import request, jsonify

def create_camera_routes(app, config, pipeline):
    """Create camera management routes"""
    
    @app.route('/api/v1/cameras', methods=['GET'])
    def get_cameras():
        """Get all cameras"""
        cameras = config.get_cameras(enabled_only=False)
        return jsonify(cameras)
    
    @app.route('/api/v1/cameras/<camera_id>', methods=['GET'])
    def get_camera(camera_id):
        """Get specific camera"""
        cameras = config.get_cameras(enabled_only=False)
        camera = next((c for c in cameras if c['camera_id'] == camera_id), None)
        
        if camera is None:
            return jsonify({"error": "Camera not found"}), 404
        
        # Add live stats if available
        if camera_id in pipeline.stream_readers:
            camera['live_stats'] = pipeline.stream_readers[camera_id].get_stats()
        
        return jsonify(camera)
    
    @app.route('/api/v1/cameras', methods=['POST'])
    def add_camera():
        """Add new camera"""
        data = request.json
        
        required = ['camera_id', 'name', 'rtsp_url']
        if not all(field in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        success = config.add_camera(
            camera_id=data['camera_id'],
            name=data['name'],
            rtsp_url=data['rtsp_url'],
            location=data.get('location'),
            frame_skip=data.get('frame_skip', 2),
            metadata=data.get('metadata')
        )
        
        if success:
            return jsonify({"message": "Camera added successfully"}), 201
        else:
            return jsonify({"error": "Camera already exists"}), 409
    
    @app.route('/api/v1/cameras/<camera_id>', methods=['PUT'])
    def update_camera(camera_id):
        """Update camera configuration"""
        data = request.json
        success = config.update_camera(camera_id, **data)
        
        if success:
            return jsonify({"message": "Camera updated successfully"})
        else:
            return jsonify({"error": "Update failed"}), 500
    
    @app.route('/api/v1/cameras/<camera_id>', methods=['DELETE'])
    def delete_camera(camera_id):
        """Delete camera"""
        success = config.delete_camera(camera_id)
        
        if success:
            if camera_id in pipeline.stream_readers:
                pipeline.stream_readers[camera_id].disconnect()
                del pipeline.stream_readers[camera_id]
                del pipeline.frame_buffers[camera_id]
            
            return jsonify({"message": "Camera deleted successfully"})
        else:
            return jsonify({"error": "Deletion failed"}), 500