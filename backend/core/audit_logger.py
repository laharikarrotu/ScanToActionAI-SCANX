"""
PHI Access Audit Logger - HIPAA Compliance
Logs all access to Protected Health Information (PHI)
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import json
import os

class AuditAction(Enum):
    """Types of PHI access actions"""
    VIEW = "view"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE = "delete"
    MODIFY = "modify"
    EXTRACT = "extract"
    PROCESS = "process"

class AuditLogger:
    """
    Logs all PHI access for HIPAA compliance
    Stores audit logs securely with retention policies
    """
    
    def __init__(self, log_file: str = "memory/audit_log.json"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def log_phi_access(
        self,
        user_id: Optional[str],
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ):
        """
        Log PHI access event
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id or "anonymous",
            "action": action.value,
            "resource_type": resource_type,  # "prescription", "image", "medical_record"
            "resource_id": resource_id,
            "ip_address": ip_address,
            "additional_info": additional_info or {}
        }
        
        # Write to audit log file
        self._write_audit_entry(audit_entry)
        
        # Also log to application logger
        self.logger.info(f"PHI Access: {action.value} {resource_type} by {user_id or 'anonymous'}")
    
    def _write_audit_entry(self, entry: Dict[str, Any]):
        """Write audit entry to log file"""
        entries = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    entries = json.load(f)
            except:
                entries = []
        
        entries.append(entry)
        
        # Keep only last 10,000 entries (configurable)
        max_entries = 10000
        if len(entries) > max_entries:
            entries = entries[-max_entries:]
        
        with open(self.log_file, "w") as f:
            json.dump(entries, f, indent=2)
    
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """
        Retrieve audit logs with filtering
        """
        if not os.path.exists(self.log_file):
            return []
        
        try:
            with open(self.log_file, "r") as f:
                entries = json.load(f)
        except:
            return []
        
        # Filter entries
        filtered = []
        for entry in entries:
            entry_date = datetime.fromisoformat(entry["timestamp"])
            
            if user_id and entry.get("user_id") != user_id:
                continue
            if action and entry.get("action") != action.value:
                continue
            if resource_type and entry.get("resource_type") != resource_type:
                continue
            if start_date and entry_date < start_date:
                continue
            if end_date and entry_date > end_date:
                continue
            
            filtered.append(entry)
        
        return filtered[-limit:]
    
    def log_image_upload(self, user_id: Optional[str], image_hash: str, ip_address: Optional[str]):
        """Log image upload"""
        self.log_phi_access(
            user_id=user_id,
            action=AuditAction.UPLOAD,
            resource_type="image",
            resource_id=image_hash,
            ip_address=ip_address,
            additional_info={"event": "image_upload"}
        )
    
    def log_prescription_extraction(self, user_id: Optional[str], image_hash: str, ip_address: Optional[str]):
        """Log prescription data extraction"""
        self.log_phi_access(
            user_id=user_id,
            action=AuditAction.EXTRACT,
            resource_type="prescription",
            resource_id=image_hash,
            ip_address=ip_address,
            additional_info={"event": "prescription_extraction"}
        )
    
    def log_data_access(self, user_id: Optional[str], resource_type: str, resource_id: str, ip_address: Optional[str]):
        """Log general data access"""
        self.log_phi_access(
            user_id=user_id,
            action=AuditAction.VIEW,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address
        )

