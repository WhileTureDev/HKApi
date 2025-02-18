from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from utils.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    fullname = Column(String)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    disabled = Column(Boolean, default=False)

    # Relationships
    deployments = relationship("Deployment", back_populates="owner")
    projects = relationship("Project", back_populates="owner")
    user_projects = relationship("UserProject", back_populates="user")
    roles = relationship("UserRole", back_populates="user")
    change_logs = relationship("ChangeLog", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
