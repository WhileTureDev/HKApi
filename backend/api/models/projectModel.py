# models/projectModel.py

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship, joinedload
from utils.database import Base  # Use absolute import

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship("User", back_populates="projects", lazy='joined')
    namespaces = relationship("Namespace", back_populates="project", lazy='joined')
    user_projects = relationship("UserProject", back_populates="project", lazy='joined')
