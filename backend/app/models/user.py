import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class UserRole:
    ADMIN = "Admin"
    SUPERVISOR = "Supervisor"
    INSPECTOR = "Inspector"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.INSPECTOR)
    organization = Column(String(150), default="Legal Metrology Department")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    inspections = relationship("Inspection", back_populates="inspector", cascade="all, delete-orphan")
