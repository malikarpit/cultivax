"""
Security Events Store

A simple in-memory ring buffer (or Redis list) to store the latest
security events (rate limits, blocked inputs) for operational visibility
in the Admin Dashboard.
"""

from collections import deque
import time
from typing import Dict, List, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class SecurityEventStore:
    def __init__(self, max_size=100):
        self.max_size = max_size
        self.events: deque = deque(maxlen=max_size)

    def add_event(self, event_type: str, details: str, request_id: str, path: str, identity: str):
        event = {
            "timestamp": time.time(),
            "type": event_type,
            "details": details,
            "request_id": request_id,
            "path": path,
            "identity": identity
        }
        self.events.appendleft(event)
        
    def get_events(self, limit: int = 50) -> List[Dict]:
        return list(self.events)[:limit]

# Singleton instance
store = SecurityEventStore()

def log_security_event(event_type: str, details: str, request_id: str, path: str, identity: str = "unknown"):
    """Helper to add an event to the global store"""
    store.add_event(event_type, details, request_id, path, identity)
    logger.warning(f"Security Event [{event_type}]: {details} (req_id={request_id}, path={path}, id={identity})")

def get_recent_security_events(limit: int = 50) -> List[Dict]:
    return store.get_events(limit)
