from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer
from utils.database import Base

class HelmRepository(Base):
    __tablename__ = "helm_repositories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
