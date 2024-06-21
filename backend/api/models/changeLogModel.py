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
    resource_name = Column(String, index=True)  # Ensure this field exists
    project_name = Column(String, index=True)  # Ensure this field exists
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String, nullable=True)
    user = relationship("User", back_populates="change_logs")
