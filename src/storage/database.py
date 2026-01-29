"""Database utilities and helpers"""

import sqlite3
from typing import List, Dict, Any, Optional
import logging

class Database:
    """
    Database utility class for common operations
    """
    
    def __init__(self, db_path: str):
        """
        Initialize database
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.logger = logging.getLogger("Database")
    
    def execute_query(
        self,
        query: str,
        params: tuple = None,
        fetch: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SQL query
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results
            
        Returns:
            List of results or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                conn.close()
                return results
            else:
                conn.commit()
                conn.close()
                return None
                
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            return None
    
    def vacuum(self) -> bool:
        """Optimize database (VACUUM)"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()
            self.logger.info("Database vacuumed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Vacuum failed: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)
    
    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def backup(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Database backed up to: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False

