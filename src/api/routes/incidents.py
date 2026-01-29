"""Incident management API routes"""

from flask import request, jsonify, send_file
import os
from pathlib import Path

def create_incident_routes(app, config, pipeline):
    """Create incident management routes"""
    
    @app.route('/api/v1/incidents', methods=['GET'])
    def get_incidents():
        """Query incidents"""
        camera_id = request.args.get('camera_id')
        incident_type = request.args.get('type')
        start_time = request.args.get('start_time', type=float)
        end_time = request.args.get('end_time', type=float)
        limit = request.args.get('limit', default=100, type=int)
        
        incidents = config.get_incidents(
            camera_id=camera_id,
            incident_type=incident_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return jsonify(incidents)
    
    @app.route('/api/v1/incidents/<int:incident_id>', methods=['GET'])
    def get_incident(incident_id):
        """Get specific incident"""
        incidents = config.get_incidents(limit=1000)
        incident = next((i for i in incidents if i['id'] == incident_id), None)
        
        if incident is None:
            return jsonify({"error": "Incident not found"}), 404
        
        return jsonify(incident)
    
    @app.route('/api/v1/incidents/stats', methods=['GET'])
    def get_incident_stats():
        """Get incident statistics"""
        hours = request.args.get('hours', default=24, type=int)
        stats = config.get_incident_statistics(hours)
        return jsonify(stats)
    
    @app.route('/api/v1/incidents/<int:incident_id>/video', methods=['GET'])
    def get_incident_video(incident_id):
        """Download incident video"""
        incidents = config.get_incidents(limit=1000)
        incident = next((i for i in incidents if i['id'] == incident_id), None)
        
        if incident is None:
            return jsonify({"error": "Incident not found"}), 404
        
        video_path = incident.get('video_path')
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({"error": "Video not available"}), 404
        
        return send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name=f"incident_{incident_id}.mp4"
        )
    
    @app.route('/api/v1/incidents/<int:incident_id>/image', methods=['GET'])
    def get_incident_image(incident_id):
        """Download incident snapshot"""
        incidents = config.get_incidents(limit=1000)
        incident = next((i for i in incidents if i['id'] == incident_id), None)
        
        if incident is None:
            return jsonify({"error": "Incident not found"}), 404
        
        image_path = incident.get('image_path')
        
        if not image_path or not os.path.exists(image_path):
            return jsonify({"error": "Image not available"}), 404
        
        return send_file(
            image_path,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=f"incident_{incident_id}.jpg"
        )
    
    @app.route('/api/v1/tracking/vehicles', methods=['GET'])
    def get_tracked_vehicles():
        """Get currently tracked vehicles"""
        camera_id = request.args.get('camera_id')
        
        if not pipeline.enable_tracking:
            return jsonify({"error": "Tracking not enabled"}), 400
        
        tracked = pipeline.get_tracked_vehicles(camera_id)
        
        # Convert to serializable format
        result = {}
        for cam_id, vehicles in tracked.items():
            result[cam_id] = []
            for track_id, vehicle in vehicles.items():
                result[cam_id].append({
                    'track_id': track_id,
                    'class_name': vehicle.class_name,
                    'bbox': vehicle.bbox,
                    'confidence': vehicle.confidence,
                    'frames_tracked': vehicle.frames_tracked,
                    'plate_text': vehicle.plate_text,
                    'incidents': vehicle.incidents,
                    'trajectory_length': len(vehicle.trajectory)
                })
        
        return jsonify(result)
    
    @app.route('/api/v1/incidents/types', methods=['GET'])
    def get_incident_types():
        """Get available incident types"""
        types = [
            {
                'type': 'no_helmet',
                'description': 'Motorcycle rider without helmet',
                'enabled': pipeline.incident_detector.enable_helmet if pipeline.incident_detector else False
            },
            {
                'type': 'no_seatbelt',
                'description': 'Car driver/passenger without seatbelt',
                'enabled': pipeline.incident_detector.enable_seatbelt if pipeline.incident_detector else False
            },
            {
                'type': 'wrong_way',
                'description': 'Vehicle traveling in wrong direction',
                'enabled': pipeline.incident_detector.enable_wrong_way if pipeline.incident_detector else False
            },
            {
                'type': 'triple_riding',
                'description': 'More than 2 people on motorcycle',
                'enabled': pipeline.incident_detector.enable_triple_riding if pipeline.incident_detector else False
            }
        ]
        
        return jsonify(types)