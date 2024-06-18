from sqlalchemy.orm import Session
from models.userModel import User
from models.roleModel import Role
from models.userRoleModel import UserRole
from utils.shared_utils import get_password_hash
import os

def initialize_db(db: Session):
    admin_username = "admin"
    admin_password = os.getenv("ADMIN_PASSWORD", "default_admin_password")

    # Create admin role if it doesn't exist
    admin_role = db.query(Role).filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(name="admin")
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)

    # Create admin user if it doesn't exist
    admin_user = db.query(User).filter_by(username=admin_username).first()
    if not admin_user:
        admin_user = User(
            username=admin_username,
            full_name="Administrator",
            email="admin@example.com",
            hashed_password=get_password_hash(admin_password),
            disabled=False
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

    # Assign admin role to admin user if not already assigned
    admin_user_role = db.query(UserRole).filter_by(user_id=admin_user.id, role_id=admin_role.id).first()
    if not admin_user_role:
        admin_user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
        db.add(admin_user_role)
        db.commit()
