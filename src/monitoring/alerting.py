"""Alerting system for critical events"""

import logging
from typing import Callable, List, Dict, Any
from enum import Enum

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class Alert:
    """Alert message"""
    
    def __init__(
        self,
        level: AlertLevel,
        message: str,
        context: Dict[str, Any] = None
    ):
        """
        Initialize alert
        
        Args:
            level: Alert severity
            message: Alert message
            context: Additional context
        """
        self.level = level
        self.message = message
        self.context = context or {}
        
        import time
        self.timestamp = time.time()

class AlertingSystem:
    """
    Alerting system
    
    Manages alerts and notifications
    """
    
    def __init__(self):
        """Initialize alerting system"""
        self.handlers: List[Callable[[Alert], None]] = []
        self.logger = logging.getLogger("AlertingSystem")
    
    def add_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add alert handler"""
        self.handlers.append(handler)
    
    def send_alert(self, alert: Alert) -> None:
        """Send alert to all handlers"""
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler failed: {e}")
    
    def info(self, message: str, context: Dict = None) -> None:
        """Send info alert"""
        self.send_alert(Alert(AlertLevel.INFO, message, context))
    
    def warning(self, message: str, context: Dict = None) -> None:
        """Send warning alert"""
        self.send_alert(Alert(AlertLevel.WARNING, message, context))
    
    def error(self, message: str, context: Dict = None) -> None:
        """Send error alert"""
        self.send_alert(Alert(AlertLevel.ERROR, message, context))
    
    def critical(self, message: str, context: Dict = None) -> None:
        """Send critical alert"""
        self.send_alert(Alert(AlertLevel.CRITICAL, message, context))


# Example alert handlers

def log_handler(alert: Alert) -> None:
    """Log alert to logger"""
    logger = logging.getLogger("AlertHandler")
    
    log_methods = {
        AlertLevel.INFO: logger.info,
        AlertLevel.WARNING: logger.warning,
        AlertLevel.ERROR: logger.error,
        AlertLevel.CRITICAL: logger.critical
    }
    
    log_method = log_methods.get(alert.level, logger.info)
    log_method(f"{alert.message} | Context: {alert.context}")


def email_handler(alert: Alert) -> None:
    """Send alert via email (placeholder)"""
    # TODO: Implement email sending
    pass


def slack_handler(alert: Alert) -> None:
    """Send alert to Slack (placeholder)"""
    # TODO: Implement Slack webhook
    pass