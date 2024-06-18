# models/userRoleModel.py
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from utils.database import Base
from models.userModel import User
from models.roleModel import Role

class UserRole(Base):
    __tablename__ = "user_roles"
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
