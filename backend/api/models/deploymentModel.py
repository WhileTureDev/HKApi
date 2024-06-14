from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from ..utils.database import Base

class Deployment(Base):
    __tablename__ = "deployments"
    id = Column(Integer, primary_key=True, index=True)
    release_type = Column(String, index=True)
    install_type = Column(String, index=True)
    chart_name = Column(String, index=True)
    chart_repo_url = Column(String, index=True)
    namespace_id = Column(Integer, ForeignKey('namespaces.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", back_populates="deployments")
    namespace = relationship("Namespace", back_populates="deployments")
