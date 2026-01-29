"""Configuration API routes"""

from flask import request, jsonify

def create_config_routes(app, config):
    """Create configuration routes"""
    
    @app.route('/api/v1/config', methods=['GET'])
    def get_config():
        """Get system configuration"""
        cfg = config.get_config()
        return jsonify(cfg)
    
    @app.route('/api/v1/config', methods=['PUT'])
    def update_config():
        """Update system configuration"""
        data = request.json
        
        for key, value in data.items():
            config.set_config(key, value)
        
        return jsonify({"message": "Configuration updated"})
    
    @app.route('/api/v1/config/<key>', methods=['GET'])
    def get_config_value(key):
        """Get specific config value"""
        value = config.get_config_value(key)
        
        if value is None:
            return jsonify({"error": "Key not found"}), 404
        
        return jsonify({key: value})
    
    @app.route('/api/v1/config/<key>', methods=['PUT'])
    def set_config_value(key):
        """Set specific config value"""
        data = request.json
        
        if 'value' not in data:
            return jsonify({"error": "Missing value"}), 400
        
        config.set_config(key, data['value'])
        return jsonify({"message": f"Config '{key}' updated"})