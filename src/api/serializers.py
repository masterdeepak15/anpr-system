"""Response serializers"""

from typing import Any, Dict, List
import json

class JSONSerializer:
    """JSON response serializer"""
    
    @staticmethod
    def serialize(data: Any) -> str:
        """Serialize data to JSON"""
        return json.dumps(data, default=str)
    
    @staticmethod
    def deserialize(json_str: str) -> Any:
        """Deserialize JSON to data"""
        return json.loads(json_str)


class ResultSerializer:
    """Serialize plate results for API responses"""
    
    @staticmethod
    def serialize_result(result) -> Dict[str, Any]:
        """Serialize single result"""
        return {
            'plate_text': result.plate_text,
            'confidence': round(result.confidence, 3),
            'camera_id': result.camera_id,
            'timestamp': result.timestamp,
            'frame_id': result.frame_id,
            'bbox': result.bbox,
            'character_confidences': [round(c, 3) for c in result.character_confidences],
            'raw_detections': result.raw_detections
        }
    
    @staticmethod
    def serialize_results(results: List) -> List[Dict[str, Any]]:
        """Serialize multiple results"""
        return [ResultSerializer.serialize_result(r) for r in results]