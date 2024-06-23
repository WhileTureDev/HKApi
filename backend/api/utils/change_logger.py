# utils/change_logger.py

from sqlalchemy.orm import Session
from models.changeLogModel import ChangeLog
from models.auditLogModel import AuditLog as AuditLogModel
from datetime import datetime


def log_change(db: Session, user_id: int, action: str, resource: str, resource_id: str, resource_name: str, project_name: str = "N/A", details: str = ""):
    change_log = ChangeLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,  # Store as string
        resource_name=resource_name,
        project_name=project_name,
        details=details
    )
    db.add(change_log)
    db.commit()
    db.refresh(change_log)

def log_audit(db: Session, action: str, user_id: int = None, details: str = None):
    audit_log = AuditLogModel(
        user_id=user_id,
        action=action,
        timestamp=datetime.utcnow(),
        details=details
    )
    db.add(audit_log)
    db.commit()
