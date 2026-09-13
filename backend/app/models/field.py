from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class InspectionField(Base):
    __tablename__ = "inspection_fields"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    extracted_value = Column(String(500), default="")
    confidence = Column(Float, default=0.0)
    status = Column(String(50), default="Found") # Found, Missing, Invalid, Low Confidence

    inspection = relationship("Inspection", back_populates="fields")
