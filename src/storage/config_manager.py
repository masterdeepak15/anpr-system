"""Configuration and data management using SQLite"""

import sqlite3
import json
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

class ConfigManager:
    """
    SQLite-based configuration and data management
    
    Handles:
    - System configuration
    - Camera configuration
    - Result storage
    - Model versioning
    """
    
    def __init__(self, db_path: str = "data/anpr_system.db"):
        """
        Initialize configuration manager
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.logger = logging.getLogger("ConfigManager")
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # System configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Camera configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cameras (
                    camera_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    rtsp_url TEXT NOT NULL,
                    location TEXT,
                    frame_skip INTEGER DEFAULT 2,
                    enabled BOOLEAN DEFAULT 1,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plate_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL,
                    plate_text TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    frame_id INTEGER,
                    bbox TEXT,
                    character_confidences TEXT,
                    raw_detections TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras(camera_id)
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_results_camera_time 
                ON plate_results(camera_id, timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_results_plate 
                ON plate_results(plate_text, timestamp DESC)
            """)
            
            # Model versions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_type TEXT NOT NULL,
                    model_path TEXT NOT NULL,
                    version TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 0,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    camera_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Incidents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_type TEXT NOT NULL,
                    track_id INTEGER NOT NULL,
                    camera_id TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    frame_id INTEGER,
                    bbox TEXT,
                    metadata TEXT,
                    video_path TEXT,
                    image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras(camera_id)
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_incidents_camera_time 
                ON incidents(camera_id, timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_incidents_type 
                ON incidents(incident_type, timestamp DESC)
            """)
            
            conn.commit()
        
        self.logger.info(f"Database initialized: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # System Configuration
    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO system_config (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, json.dumps(value)))
            conn.commit()
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_config WHERE key = ?", (key,))
            row = cursor.fetchone()
            
            if row:
                return json.loads(row["value"])
            return default
    
    def get_config(self) -> Dict[str, Any]:
        """Get all configuration"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM system_config")
            rows = cursor.fetchall()
            
            config = {}
            for row in rows:
                config[row["key"]] = json.loads(row["value"])
            
            return config
    
    # Camera Management
    def add_camera(
        self,
        camera_id: str,
        name: str,
        rtsp_url: str,
        location: str = None,
        frame_skip: int = 2,
        metadata: Dict = None
    ) -> bool:
        """Add a new camera"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO cameras (camera_id, name, rtsp_url, location, frame_skip, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    camera_id, name, rtsp_url, location, frame_skip,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
            
            self.logger.info(f"Camera added: {camera_id}")
            return True
        except sqlite3.IntegrityError:
            self.logger.error(f"Camera already exists: {camera_id}")
            return False
    
    def get_cameras(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """Get all cameras"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if enabled_only:
                cursor.execute("SELECT * FROM cameras WHERE enabled = 1")
            else:
                cursor.execute("SELECT * FROM cameras")
            
            rows = cursor.fetchall()
            
            cameras = []
            for row in rows:
                camera = dict(row)
                if camera["metadata"]:
                    camera["metadata"] = json.loads(camera["metadata"])
                cameras.append(camera)
            
            return cameras
    
    def update_camera(self, camera_id: str, **kwargs) -> bool:
        """Update camera configuration"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                fields = []
                values = []
                
                for key, value in kwargs.items():
                    if key == "metadata":
                        value = json.dumps(value)
                    fields.append(f"{key} = ?")
                    values.append(value)
                
                fields.append("updated_at = CURRENT_TIMESTAMP")
                values.append(camera_id)
                
                query = f"UPDATE cameras SET {', '.join(fields)} WHERE camera_id = ?"
                cursor.execute(query, values)
                conn.commit()
            
            return True
        except Exception as e:
            self.logger.error(f"Camera update failed: {e}")
            return False
    
    def delete_camera(self, camera_id: str) -> bool:
        """Delete a camera"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cameras WHERE camera_id = ?", (camera_id,))
                conn.commit()
            
            self.logger.info(f"Camera deleted: {camera_id}")
            return True
        except Exception as e:
            self.logger.error(f"Camera deletion failed: {e}")
            return False
    
    # Result Storage
    def save_result(self, result) -> bool:
        """Save a plate recognition result"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO plate_results (
                        camera_id, plate_text, confidence, timestamp, frame_id,
                        bbox, character_confidences, raw_detections
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.camera_id, result.plate_text, result.confidence,
                    result.timestamp, result.frame_id,
                    json.dumps(result.bbox),
                    json.dumps(result.character_confidences),
                    json.dumps(result.raw_detections)
                ))
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Result save failed: {e}")
            return False
    
    def get_results(
        self,
        camera_id: str = None,
        start_time: float = None,
        end_time: float = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query plate results"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM plate_results WHERE 1=1"
            params = []
            
            if camera_id:
                query += " AND camera_id = ?"
                params.append(camera_id)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                result = dict(row)
                result["bbox"] = json.loads(result["bbox"]) if result["bbox"] else None
                result["character_confidences"] = json.loads(result["character_confidences"]) if result["character_confidences"] else []
                result["raw_detections"] = json.loads(result["raw_detections"]) if result["raw_detections"] else []
                results.append(result)
            
            return results
    
    def log_metric(self, metric_name: str, metric_value: float, camera_id: str = None) -> None:
        """Log a metric"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO metrics (metric_name, metric_value, camera_id)
                VALUES (?, ?, ?)
            """, (metric_name, metric_value, camera_id))
            conn.commit()

    # Incident Management
    def save_incident(self, incident) -> bool:
        """Save incident to database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO incidents (
                        incident_type, track_id, camera_id, confidence,
                        timestamp, frame_id, bbox, metadata, video_path, image_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    incident.incident_type,
                    incident.track_id,
                    incident.camera_id,
                    incident.confidence,
                    incident.timestamp,
                    incident.frame_id,
                    json.dumps(incident.bbox),
                    json.dumps(incident.metadata),
                    None,  # video_path (will be updated later)
                    None   # image_path (will be updated later)
                ))
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Incident save failed: {e}")
            return False

    def update_incident_video_path(self, incident, video_path: str) -> bool:
        """Update incident with video path"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get the incident ID (most recent for this track/camera/timestamp)
                cursor.execute("""
                    SELECT id FROM incidents 
                    WHERE track_id = ? AND camera_id = ? AND timestamp = ?
                    ORDER BY id DESC LIMIT 1
                """, (incident.track_id, incident.camera_id, incident.timestamp))
                
                row = cursor.fetchone()
                if row:
                    incident_id = row["id"]
                    
                    # Update with video path
                    cursor.execute("""
                        UPDATE incidents 
                        SET video_path = ?, image_path = ?
                        WHERE id = ?
                    """, (
                        video_path,
                        video_path.replace('.mp4', '.jpg'),
                        incident_id
                    ))
                    conn.commit()
                    return True
            
            return False
        except Exception as e:
            self.logger.error(f"Incident video path update failed: {e}")
            return False

    def get_incidents(
        self,
        camera_id: str = None,
        incident_type: str = None,
        start_time: float = None,
        end_time: float = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query incidents"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM incidents WHERE 1=1"
            params = []
            
            if camera_id:
                query += " AND camera_id = ?"
                params.append(camera_id)
            
            if incident_type:
                query += " AND incident_type = ?"
                params.append(incident_type)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            incidents = []
            for row in rows:
                incident = dict(row)
                incident["bbox"] = json.loads(incident["bbox"]) if incident["bbox"] else None
                incident["metadata"] = json.loads(incident["metadata"]) if incident["metadata"] else {}
                incidents.append(incident)
            
            return incidents

    def get_incident_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get incident statistics"""
        cutoff_time = time.time() - hours * 3600
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total incidents
            cursor.execute("""
                SELECT COUNT(*) as count FROM incidents WHERE timestamp >= ?
            """, (cutoff_time,))
            total = cursor.fetchone()['count']
            
            # Per-type breakdown
            cursor.execute("""
                SELECT incident_type, COUNT(*) as count
                FROM incidents
                WHERE timestamp >= ?
                GROUP BY incident_type
            """, (cutoff_time,))
            per_type = {row['incident_type']: row['count'] for row in cursor.fetchall()}
            
            # Per-camera breakdown
            cursor.execute("""
                SELECT camera_id, COUNT(*) as count
                FROM incidents
                WHERE timestamp >= ?
                GROUP BY camera_id
            """, (cutoff_time,))
            per_camera = {row['camera_id']: row['count'] for row in cursor.fetchall()}
            
            return {
                "hours": hours,
                "total_incidents": total,
                "per_type": per_type,
                "per_camera": per_camera
            }