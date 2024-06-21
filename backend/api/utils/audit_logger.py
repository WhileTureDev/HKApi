import logging
from sqlalchemy.orm import Session
from models.auditLogModel import AuditLog as AuditLogModel

logger = logging.getLogger(__name__)

def log_audit(db: Session, user_id: int, action: str, resource: str = "user", resource_id: int = None, resource_name: str = "N/A", details: str = None):
    try:
        audit_log = AuditLogModel(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            resource_name=resource_name,
            details=details
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        logger.error(f"Error logging audit: {e}")
        db.rollback()
        raise e
