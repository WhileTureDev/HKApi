from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from utils.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String, index=True)
    resource = Column(String, index=True, default='user')
    resource_id = Column(Integer, index=True, nullable=True)
    resource_name = Column(String, index=True, default='N/A')
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String, nullable=True)
    user = relationship("User", back_populates="audit_logs")
