"""
Database logger - stores events in Supabase/Postgres
"""
from typing import Dict, Any, Optional
from datetime import datetime
from memory.database import SessionLocal, ScanRequest, UISchema, ActionPlan, ExecutionResult
import json

class DatabaseLogger:
    """Logger that stores events in database instead of JSON file"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def log_scan_request(
        self,
        image_hash: str,
        intent: str,
        session_id: Optional[str] = None
    ) -> int:
        """Log a scan request and return the ID"""
        scan = ScanRequest(
            session_id=session_id,
            image_hash=image_hash,
            intent=intent
        )
        self.db.add(scan)
        self.db.commit()
        self.db.refresh(scan)
        return scan.id
    
    def log_ui_schema(
        self,
        ui_schema: Dict[str, Any],
        scan_request_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> int:
        """Log UI schema"""
        # Redact sensitive info
        redacted = self._redact_sensitive(ui_schema)
        
        schema = UISchema(
            scan_request_id=scan_request_id,
            session_id=session_id,
            page_type=redacted.get("page_type", "unknown"),
            url_hint=redacted.get("url_hint"),
            elements=redacted.get("elements", [])
        )
        self.db.add(schema)
        self.db.commit()
        self.db.refresh(schema)
        return schema.id
    
    def log_action_plan(
        self,
        plan: Dict[str, Any],
        scan_request_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> int:
        """Log action plan"""
        action_plan = ActionPlan(
            scan_request_id=scan_request_id,
            session_id=session_id,
            task=plan.get("task", "unknown"),
            steps=plan.get("steps", []),
            estimated_time=plan.get("estimated_time")
        )
        self.db.add(action_plan)
        self.db.commit()
        self.db.refresh(action_plan)
        return action_plan.id
    
    def log_execution_result(
        self,
        result: Dict[str, Any],
        action_plan_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> int:
        """Log execution result"""
        exec_result = ExecutionResult(
            action_plan_id=action_plan_id,
            session_id=session_id,
            status=result.get("status", "unknown"),
            message=result.get("message", ""),
            final_url=result.get("final_url"),
            screenshot_path=result.get("screenshot_path"),
            error=result.get("error"),
            logs=result.get("logs", [])
        )
        self.db.add(exec_result)
        self.db.commit()
        self.db.refresh(exec_result)
        return exec_result.id
    
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
    
    def close(self):
        """Close database session"""
        self.db.close()

