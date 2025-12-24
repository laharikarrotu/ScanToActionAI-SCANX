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
    Stores audit logs in database (preferred) or JSON file (fallback)
    """
    
    def __init__(self, log_file: str = "memory/audit_log.json", use_database: bool = True):
        self.log_file = log_file
        self.use_database = use_database
        self.logger = logging.getLogger(__name__)
        
        # Try to use database if available
        self.db_available = False
        if use_database:
            try:
                from memory.database import SessionLocal, AuditLog
                self.SessionLocal = SessionLocal
                self.AuditLog = AuditLog
                self.db_available = True
                self.logger.info("Using database for audit logs")
            except Exception as e:
                self.logger.warning(f"Database not available for audit logs: {e}. Falling back to JSON file.")
                self.db_available = False
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        if not self.db_available:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
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
        
        # Write to database (preferred) or file (fallback)
        if self.db_available:
            self._write_to_database(audit_entry)
        else:
            self._write_to_file(audit_entry)
        
        # Also log to application logger
        self.logger.info(f"PHI Access: {action.value} {resource_type} by {user_id or 'anonymous'}")
    
    def _write_to_database(self, entry: Dict[str, Any]):
        """Write audit entry to database"""
        try:
            db = self.SessionLocal()
            try:
                audit_log = self.AuditLog(
                    timestamp=datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00')) if isinstance(entry["timestamp"], str) else entry["timestamp"],
                    user_id=entry["user_id"],
                    action=entry["action"],
                    resource_type=entry["resource_type"],
                    resource_id=entry.get("resource_id"),
                    ip_address=entry.get("ip_address"),
                    additional_info=entry.get("additional_info")
                )
                db.add(audit_log)
                db.commit()
            except Exception as e:
                db.rollback()
                self.logger.error(f"Failed to write audit log to database: {e}", exc_info=True)
                # Fallback to file
                self._write_to_file(entry)
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"Database audit logging failed: {e}", exc_info=True)
            # Fallback to file
            self._write_to_file(entry)
    
    def _write_to_file(self, entry: Dict[str, Any]):
        """Write audit entry to JSON file (fallback)"""
        entries = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    entries = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, IOError):
                entries = []
        
        entries.append(entry)
        
        # Keep only last 10,000 entries (configurable)
        max_entries = 10000
        if len(entries) > max_entries:
            entries = entries[-max_entries:]
        
        try:
            with open(self.log_file, "w") as f:
                json.dump(entries, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to write audit log to file: {e}", exc_info=True)
    
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
        if self.db_available:
            return self._get_from_database(user_id, action, resource_type, start_date, end_date, limit)
        else:
            return self._get_from_file(user_id, action, resource_type, start_date, end_date, limit)
    
    def _get_from_database(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """Retrieve audit logs from database"""
        try:
            db = self.SessionLocal()
            try:
                query = db.query(self.AuditLog)
                
                if user_id:
                    query = query.filter(self.AuditLog.user_id == user_id)
                if action:
                    query = query.filter(self.AuditLog.action == action.value)
                if resource_type:
                    query = query.filter(self.AuditLog.resource_type == resource_type)
                if start_date:
                    query = query.filter(self.AuditLog.timestamp >= start_date)
                if end_date:
                    query = query.filter(self.AuditLog.timestamp <= end_date)
                
                logs = query.order_by(self.AuditLog.timestamp.desc()).limit(limit).all()
                
                # Convert to dict format
                return [{
                    "timestamp": log.timestamp.isoformat(),
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "ip_address": log.ip_address,
                    "additional_info": log.additional_info
                } for log in logs]
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"Failed to retrieve audit logs from database: {e}", exc_info=True)
            # Fallback to file
            return self._get_from_file(user_id, action, resource_type, start_date, end_date, limit)
    
    def _get_from_file(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """Retrieve audit logs from JSON file (fallback)"""
        if not os.path.exists(self.log_file):
            return []
        
        try:
            with open(self.log_file, "r") as f:
                entries = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, IOError):
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

