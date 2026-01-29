"""Results query API routes"""

from flask import request, jsonify
import time

def create_result_routes(app, config):
    """Create result query routes"""
    
    @app.route('/api/v1/results', methods=['GET'])
    def get_results():
        """Query plate results"""
        camera_id = request.args.get('camera_id')
        start_time = request.args.get('start_time', type=float)
        end_time = request.args.get('end_time', type=float)
        limit = request.args.get('limit', default=100, type=int)
        
        results = config.get_results(
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return jsonify(results)
    
    @app.route('/api/v1/results/search', methods=['GET'])
    def search_results():
        """Search for specific plate"""
        plate = request.args.get('plate')
        
        if not plate:
            return jsonify({"error": "Missing plate parameter"}), 400
        
        # Use database connection
        import sqlite3
        conn = sqlite3.connect(config.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM plate_results 
            WHERE plate_text LIKE ?
            ORDER BY timestamp DESC
            LIMIT 100
        """, (f"%{plate}%",))
        
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        conn.close()
        
        return jsonify(results)
    
    @app.route('/api/v1/results/stats', methods=['GET'])
    def get_result_stats():
        """Get result statistics"""
        hours = request.args.get('hours', default=24, type=int)
        cutoff_time = time.time() - hours * 3600
        
        import sqlite3
        conn = sqlite3.connect(config.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Total detections
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM plate_results 
            WHERE timestamp >= ?
        """, (cutoff_time,))
        total = cursor.fetchone()['count']
        
        # Per-camera breakdown
        cursor.execute("""
            SELECT camera_id, COUNT(*) as count
            FROM plate_results
            WHERE timestamp >= ?
            GROUP BY camera_id
        """, (cutoff_time,))
        per_camera = {row['camera_id']: row['count'] for row in cursor.fetchall()}
        
        # Average confidence
        cursor.execute("""
            SELECT AVG(confidence) as avg_conf
            FROM plate_results
            WHERE timestamp >= ?
        """, (cutoff_time,))
        avg_conf = cursor.fetchone()['avg_conf'] or 0.0
        
        conn.close()
        
        return jsonify({
            "hours": hours,
            "total_detections": total,
            "per_camera": per_camera,
            "average_confidence": avg_conf
        })