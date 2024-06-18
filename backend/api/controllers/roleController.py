# controllers/roleController.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.roleModel import Role
from models.userRoleModel import UserRole
from models.userModel import User
from utils.database import get_db
from utils.auth import get_current_active_user

router = APIRouter()


@router.post("/roles", response_model=dict)
def create_role(name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    role = db.query(Role).filter_by(name=name).first()
    if role:
        raise HTTPException(status_code=400, detail="Role already exists")

    new_role = Role(name=name)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return {"message": "Role created successfully", "role": new_role.name}


@router.post("/roles/assign", response_model=dict)
def assign_role(user_id: int, role_name: str, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_active_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter_by(name=role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    user_role = db.query(UserRole).filter_by(user_id=user_id, role_id=role.id).first()
    if user_role:
        raise HTTPException(status_code=400, detail="User already has this role")

    new_user_role = UserRole(user_id=user_id, role_id=role.id)
    db.add(new_user_role)
    db.commit()
    return {"message": "Role assigned successfully"}
