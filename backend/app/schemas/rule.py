from pydantic import BaseModel
from typing import Optional

class RuleBase(BaseModel):
    rule_id: str
    field: str
    description: str
    required: bool = True
    severity: str = "HIGH"
    active: bool = True
    reference: str

class RuleCreate(RuleBase):
    pass

class RuleResponse(RuleBase):
    id: int

    class Config:
        from_attributes = True
