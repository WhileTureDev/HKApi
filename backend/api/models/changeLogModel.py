from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from utils.database import Base
from datetime import datetime

class ChangeLog(Base):
    __tablename__ = "change_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User")
    action = Column(String, index=True)
    resource = Column(String, index=True)
    resource_id = Column(String, index=True)  # Change this to String
    resource_name = Column(String, index=True)
    project_name = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String)
