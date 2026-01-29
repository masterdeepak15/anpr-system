# ANPR System - API Examples with Tracking & Incidents

## Incident Management

### Get All Incidents
```bash
curl http://localhost:5000/api/v1/incidents?limit=50
```

### Get Incidents by Type
```bash
# No helmet incidents
curl http://localhost:5000/api/v1/incidents?type=no_helmet

# Wrong way incidents
curl http://localhost:5000/api/v1/incidents?type=wrong_way

# Triple riding incidents
curl http://localhost:5000/api/v1/incidents?type=triple_riding
```

### Get Incidents by Camera
```bash
curl http://localhost:5000/api/v1/incidents?camera_id=cam_entrance_01
```

### Get Incident Statistics
```bash
# Last 24 hours
curl http://localhost:5000/api/v1/incidents/stats?hours=24

# Last week
curl http://localhost:5000/api/v1/incidents/stats?hours=168
```

### Download Incident Video
```bash
curl http://localhost:5000/api/v1/incidents/123/video -o incident_123.mp4
```

### Download Incident Snapshot
```bash
curl http://localhost:5000/api/v1/incidents/123/image -o incident_123.jpg
```

### Get Specific Incident
```bash
curl http://localhost:5000/api/v1/incidents/123
```

**Response:**
```json
{
  "id": 123,
  "incident_type": "no_helmet",
  "track_id": 42,
  "camera_id": "cam_entrance_01",
  "confidence": 0.89,
  "timestamp": 1706543210.123,
  "frame_id": 1250,
  "bbox": [120, 200, 320, 480],
  "metadata": {
    "vehicle_class": "motorcycle",
    "plate": "MH12AB1234",
    "rider_count": 2
  },
  "video_path": "incidents/cam_entrance_01_no_helmet_42_1706543210.mp4",
  "image_path": "incidents/cam_entrance_01_no_helmet_42_1706543210.jpg"
}
```

## Vehicle Tracking

### Get Currently Tracked Vehicles
```bash
# All cameras
curl http://localhost:5000/api/v1/tracking/vehicles

# Specific camera
curl http://localhost:5000/api/v1/tracking/vehicles?camera_id=cam_entrance_01
```

**Response:**
```json
{
  "cam_entrance_01": [
    {
      "track_id": 42,
      "class_name": "motorcycle",
      "bbox": [120, 200, 320, 480],
      "confidence": 0.92,
      "frames_tracked": 45,
      "plate_text": "MH12AB1234",
      "incidents": ["no_helmet"],
      "trajectory_length": 30
    },
    {
      "track_id": 43,
      "class_name": "car",
      "bbox": [500, 150, 800, 450],
      "confidence": 0.95,
      "frames_tracked": 120,
      "plate_text": "DL8CAA9999",
      "incidents": [],
      "trajectory_length": 30
    }
  ]
}
```

### Get Incident Types
```bash
curl http://localhost:5000/api/v1/incidents/types
```

**Response:**
```json
[
  {
    "type": "no_helmet",
    "description": "Motorcycle rider without helmet",
    "enabled": true
  },
  {
    "type": "no_seatbelt",
    "description": "Car driver/passenger without seatbelt",
    "enabled": true
  },
  {
    "type": "wrong_way",
    "description": "Vehicle traveling in wrong direction",
    "enabled": true
  },
  {
    "type": "triple_riding",
    "description": "More than 2 people on motorcycle",
    "enabled": true
  }
]
```

## Real-Time Event Stream (SSE)

### Listen for Incidents
```bash
curl -N http://localhost:5000/api/v1/events/stream
```

**Events received:**
```
data: {"type": "incident_detected", "timestamp": 1706543210.123, "data": {"incident_type": "no_helmet", "track_id": 42, "camera_id": "cam_entrance_01", "confidence": 0.89}}

data: {"type": "plate_detected", "timestamp": 1706543215.456, "data": {"camera_id": "cam_entrance_01", "plate_text": "MH12AB1234", "confidence": 0.92}}

data: {"type": "incident_detected", "timestamp": 1706543220.789, "data": {"incident_type": "wrong_way", "track_id": 45, "camera_id": "cam_exit_01", "confidence": 0.95}}
```

## Python Client Example
```python
import requests
import json

API_BASE = "http://localhost:5000"

# Get recent incidents
response = requests.get(f"{API_BASE}/api/v1/incidents", params={"limit": 10})
incidents = response.json()

for incident in incidents:
    print(f"Incident: {incident['incident_type']}")
    print(f"  Track ID: {incident['track_id']}")
    print(f"  Camera: {incident['camera_id']}")
    print(f"  Confidence: {incident['confidence']:.2f}")
    
    if incident['video_path']:
        # Download video
        video_response = requests.get(
            f"{API_BASE}/api/v1/incidents/{incident['id']}/video"
        )
        
        with open(f"incident_{incident['id']}.mp4", 'wb') as f:
            f.write(video_response.content)
        
        print(f"  Video saved: incident_{incident['id']}.mp4")
    
    print()
```

## JavaScript Client Example (SSE)
```javascript
const eventSource = new EventSource('http://localhost:5000/api/v1/events/stream');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'incident_detected') {
        console.log('🚨 INCIDENT:', data.data.incident_type);
        console.log('Track ID:', data.data.track_id);
        console.log('Camera:', data.data.camera_id);
        console.log('Confidence:', data.data.confidence);
        
        // Show alert or notification
        showIncidentAlert(data.data);
    }
};

eventSource.onerror = function(error) {
    console.error('SSE Error:', error);
};
```