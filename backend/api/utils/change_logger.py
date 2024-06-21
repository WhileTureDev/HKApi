# utils/change_logger.py

from sqlalchemy.orm import Session
from models.changeLogModel import ChangeLog as ChangeLogModel
from models.auditLogModel import AuditLog as AuditLogModel
from datetime import datetime


def log_change(db: Session, user_id: int, action: str, resource: str, resource_id: int, resource_name: str, project_name: str, details: str = None):
    log_entry = ChangeLogModel(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        resource_name=resource_name,
        project_name=project_name,
        timestamp=datetime.utcnow(),
        details=details
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

def log_audit(db: Session, action: str, user_id: int = None, details: str = None):
    audit_log = AuditLogModel(
        user_id=user_id,
        action=action,
        timestamp=datetime.utcnow(),
        details=details
    )
    db.add(audit_log)
    db.commit()
