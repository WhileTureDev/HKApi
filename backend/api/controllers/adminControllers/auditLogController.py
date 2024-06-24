import logging
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
)
from models.auditLogModel import AuditLog as AuditLogModel
from models.userModel import User as UserModel
from schemas.auditLogSchema import AuditLog as AuditLogSchema
from utils.database import get_db
from utils.error_handling import handle_general_exception
from utils.security import get_current_user_roles, is_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/admin/audit_logs", response_model=List[AuditLogSchema])
async def get_all_audit_logs(
        db: Session = Depends(get_db),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    method = "GET"
    endpoint = "/admin/audit_logs"
    start_time = time.time()
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    if not is_admin(current_user_roles):
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        audit_logs = db.query(AuditLogModel).all()
        logger.debug(f"Fetched {len(audit_logs)} audit logs from the database")

        result = []
        for log in audit_logs:
            try:
                user = db.query(UserModel).filter(UserModel.id == log.user_id).first()
                result.append({
                    "id": log.id,
                    "user_id": log.user_id,
                    "user_name": user.username if user else "Unknown",
                    "action": log.action,
                    "resource": log.resource,
                    "resource_id": log.resource_id,
                    "resource_name": log.resource_name,
                    "timestamp": log.timestamp,
                    "details": log.details
                })
            except Exception as e:
                logger.error(f"Error processing log entry {log.id}: {e}")
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        handle_general_exception(e)
    finally:
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
        IN_PROGRESS.labels(endpoint=endpoint).dec()
