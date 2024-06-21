from sqlalchemy.orm import Session
from models.changeLogModel import ChangeLog

def log_change(db: Session, user_id: int, action: str, resource: str, resource_id: int, resource_name: str, project_name: str, details: str = None):
    change_log = ChangeLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        resource_name=resource_name,
        project_name=project_name,
        details=details
    )
    db.add(change_log)
    db.commit()
