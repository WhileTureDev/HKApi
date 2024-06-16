from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from utils.database import Base

class Namespace(Base):
    __tablename__ = "namespaces"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'))
    owner_id = Column(Integer, ForeignKey('users.id'))  # New field for owner
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="namespaces")
    deployments = relationship("Deployment", back_populates="namespace")
