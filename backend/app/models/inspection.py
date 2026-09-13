import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(100), unique=True, index=True, nullable=True) # Unique statutory inspection reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    product_name = Column(String(200), default="Packaged Commodity")
    image_path = Column(String(500), nullable=False) # Uploaded image reference
    inspection_date = Column(DateTime, default=datetime.datetime.utcnow) # Inspection date/time
    compliance_status = Column(String(50), nullable=False, index=True) # COMPLIANT, NON-COMPLIANT, REVIEW REQUIRED, PARTIALLY COMPLIANT
    compliance_score = Column(Float, default=0.0) # Calibrated compliance score (0.0 - 100.0%)
    raw_ocr_text = Column(Text, default="")
    ocr_info = Column(JSON, default=dict) # Full OCR information (text, boxes, confidence, regions)
    extracted_data = Column(JSON, default=dict) # Extracted statutory declarations
    rule_results = Column(JSON, default=list) # Evaluated legal rule outcomes
    violations = Column(JSON, default=list) # Detected statutory infractions
    quality_score = Column(Float, default=100.0)
    quality_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    inspector = relationship("User", back_populates="inspections")
    fields = relationship("InspectionField", back_populates="inspection", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="inspection", cascade="all, delete-orphan")

    @property
    def uploaded_image_reference(self) -> str:
        """Alias for uploaded image reference."""
        return self.image_path

    @property
    def image_reference(self) -> str:
        """Alias for uploaded image reference."""
        return self.image_path

    @property
    def date_time(self) -> datetime.datetime:
        """Alias for inspection date/time."""
        return self.created_at or self.inspection_date or datetime.datetime.utcnow()

    @property
    def extracted_declarations(self) -> dict:
        """Alias for extracted declarations dictionary."""
        return self.extracted_data or {}

    @property
    def ocr_information(self) -> dict:
        """Alias for OCR information dictionary."""
        if self.ocr_info and isinstance(self.ocr_info, dict):
            return self.ocr_info
        return {
            "raw_text": self.raw_ocr_text or "",
            "bounding_boxes": (self.extracted_data or {}).get("_bounding_boxes", [])
        }

    def to_persistence_dict(self) -> dict:
        """
        Serializes inspection into self-contained statutory record dictionary
        containing all 9 required persistence items.
        """
        dt = self.date_time
        iso_dt = dt.isoformat() if hasattr(dt, "isoformat") else str(dt)

        return {
            "inspection_id": self.inspection_id or str(self.id),
            "id": self.id,
            "uploaded_image_reference": self.image_path,
            "image_reference": self.image_path,
            "date_time": iso_dt,
            "datetime": iso_dt,
            "extracted_declarations": self.extracted_declarations,
            "ocr_information": self.ocr_information,
            "rule_results": self.rule_results or [],
            "violations": self.violations or [],
            "compliance_status": self.compliance_status,
            "compliance_score": self.compliance_score
        }
