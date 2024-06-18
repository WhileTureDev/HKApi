# models/roleModel.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from utils.database import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    users = relationship("UserRole", back_populates="role")
