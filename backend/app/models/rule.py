from sqlalchemy import Column, Integer, String, Boolean, Text
from app.database import Base

class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(50), unique=True, index=True, nullable=False) # e.g. "PCR-2011-R6-1-A"
    field = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    required = Column(Boolean, default=True)
    severity = Column(String(20), default="HIGH") # HIGH, MEDIUM, LOW
    active = Column(Boolean, default=True)
    reference = Column(String(200), nullable=False) # "Rule 6(1)(a), Packaged Commodities Rules, 2011"
