from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Boolean
from sqlalchemy.orm import relationship
from utils.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    disabled = Column(Boolean, default=False)
    deployments = relationship("Deployment", back_populates="owner")
    projects = relationship("Project", back_populates="owner")
    user_projects = relationship("UserProject", back_populates="user")
    roles = relationship("UserRole", back_populates="user")
    change_logs = relationship("ChangeLog", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")  # New relationship
