import datetime
from pydantic import BaseModel

class ReportResponse(BaseModel):
    id: int
    inspection_id: int
    product_name: str
    compliance_status: str
    compliance_score: float
    report_url: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True
