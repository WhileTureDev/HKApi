# controllers/auditLogController.py

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models.auditLogModel import AuditLog as AuditLogModel
from schemas.auditLogSchema import AuditLog as AuditLogSchema
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel
from utils.security import get_current_user_roles, is_admin
from utils.circuit_breaker import call_database_operation  # Import the circuit breaker

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/auditlogs", response_model=List[AuditLogSchema])
async def get_all_audit_logs(
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    if not is_admin(current_user_roles):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        audit_logs = call_database_operation(db.query(AuditLogModel).all)
        logger.debug(f"Fetched {len(audit_logs)} audit logs from the database")

        result = []
        for log in audit_logs:
            try:
                user = call_database_operation(db.query(UserModel).filter(UserModel.id == log.user_id).first) if log.user_id else None
                result.append({
                    "id": log.id,
                    "user_id": log.user_id,
                    "user_name": user.username if user else "Unknown",
                    "action": log.action,
                    "timestamp": log.timestamp,
                    "details": log.details
                })
            except Exception as e:
                logger.error(f"Error processing log entry {log.id}: {e}")

        return result
    except Exception as e:
        logger.error(f"Error querying audit logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying audit logs: {str(e)}")
