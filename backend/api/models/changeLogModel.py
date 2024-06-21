# models/changeLogModel.py

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from utils.database import Base

class ChangeLog(Base):
    __tablename__ = "change_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String, index=True)
    resource = Column(String, index=True)
    resource_id = Column(Integer, index=True)
    resource_name = Column(String, index=True)  # New field
    project_name = Column(String, index=True)  # New field
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String, nullable=True)
    user = relationship("User", back_populates="change_logs")


# controllers/changeLogController.py

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models.changeLogModel import ChangeLog as ChangeLogModel
from schemas.changeLogSchema import ChangeLog as ChangeLogSchema
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel
from utils.security import get_current_user_roles, is_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/changelogs", response_model=List[ChangeLogSchema])
async def get_all_change_logs(
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    if not is_admin(current_user_roles):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    change_logs = db.query(ChangeLogModel).all()
    return change_logs

@router.get("/changelogs/user/{user_id}", response_model=List[ChangeLogSchema])
async def get_change_logs_for_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    if not is_admin(current_user_roles) and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    change_logs = db.query(ChangeLogModel).filter(ChangeLogModel.user_id == user_id).all()
    return change_logs

@router.get("/changelogs/resource/{resource}/{resource_name}", response_model=List[ChangeLogSchema])
async def get_change_logs_for_resource(
        resource: str,
        resource_name: str,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    if not is_admin(current_user_roles):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    change_logs = db.query(ChangeLogModel).filter(ChangeLogModel.resource == resource, ChangeLogModel.resource_name == resource_name).all()
    return change_logs
