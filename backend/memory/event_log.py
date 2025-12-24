"""
Memory/Storage - Simple event logging for now
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class EventLogger:
    def __init__(self, log_file: str = "memory/event_log.json"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    def log_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        session_id: Optional[str] = None
    ):
        """Append event to log file"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "session_id": session_id,
            "data": data
        }
        
        # Read existing logs
        events = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    events = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, IOError):
                events = []
        
        # Append new event
        events.append(event)
        
        # Write back
        with open(self.log_file, "w") as f:
            json.dump(events, f, indent=2)
    
    def log_scan_request(
        self,
        image_hash: str,
        intent: str,
        session_id: Optional[str] = None
    ):
        """Log a scan request"""
        self.log_event(
            "scan_request",
            {
                "image_hash": image_hash,
                "intent": intent
            },
            session_id
        )
    
    def log_ui_schema(
        self,
        ui_schema: Dict[str, Any],
        session_id: Optional[str] = None
    ):
        """Log UI schema (redacted)"""
        # Redact sensitive info
        redacted = self._redact_sensitive(ui_schema)
        self.log_event("ui_schema", redacted, session_id)
    
    def log_action_plan(
        self,
        plan: Dict[str, Any],
        session_id: Optional[str] = None
    ):
        """Log action plan"""
        self.log_event("action_plan", plan, session_id)
    
    def log_execution_result(
        self,
        result: Dict[str, Any],
        session_id: Optional[str] = None
    ):
        """Log execution result"""
        self.log_event("execution_result", result, session_id)
    
    def _redact_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive fields from data"""
        sensitive_patterns = [
            "password", "card", "cvv", "ssn", "credit", "cvc"
        ]
        
        if isinstance(data, dict):
            redacted = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(pattern in key_lower for pattern in sensitive_patterns):
                    redacted[key] = "***REDACTED***"
                elif isinstance(value, (dict, list)):
                    redacted[key] = self._redact_sensitive(value)
                else:
                    redacted[key] = value
            return redacted
        elif isinstance(data, list):
            return [self._redact_sensitive(item) for item in data]
        else:
            return data

