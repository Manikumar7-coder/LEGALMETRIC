import datetime
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QualityReportSchema(BaseModel):
    is_acceptable: bool = True
    blur_score: float = 0.0
    brightness_score: float = 0.0
    contrast_score: float = 0.0
    warnings: List[str] = []
    message: str = "Image quality is optimal for compliance analysis."

class InspectionFieldSchema(BaseModel):
    field_name: str
    extracted_value: str
    confidence: float
    status: str # Found, Missing, Invalid, Low Confidence

    class Config:
        from_attributes = True

class ViolationSchema(BaseModel):
    field: str
    issue: str
    severity: str # HIGH, MEDIUM, LOW
    rule_reference: str
    recommendation: str

class InspectionResponse(BaseModel):
    id: int
    user_id: int
    product_name: str
    image_url: str
    inspection_date: datetime.datetime
    compliance_status: str # COMPLIANT, NON-COMPLIANT, REVIEW REQUIRED, PARTIALLY COMPLIANT
    compliance_score: float
    violations_count: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class InspectionDetailResponse(BaseModel):
    id: int
    user_id: int
    product_name: str
    image_url: str
    inspection_date: datetime.datetime
    compliance_status: str
    compliance_score: float
    raw_ocr_text: str
    extracted_data: Dict[str, Any]
    violations: List[ViolationSchema]
    fields: List[InspectionFieldSchema]
    quality_score: float
    quality_notes: str
    bounding_boxes: List[Dict[str, Any]] = []
    has_report: bool = False
    report_id: Optional[int] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class DashboardStatsResponse(BaseModel):
    total_inspections: int
    compliant_count: int
    non_compliant_count: int
    review_required_count: int
    compliance_percentage: float
    recent_inspections: List[Dict[str, Any]]
    trend_data: List[Dict[str, Any]]
    violations_breakdown: Dict[str, int]
