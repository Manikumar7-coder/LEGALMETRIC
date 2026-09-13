from fastapi import APIRouter
from app.rules.rule_engine import rule_engine

router = APIRouter(prefix="/api/rules", tags=["Legal Metrology Rules"])

@router.get("")
def get_rules():
    """
    Returns the active statutory rule specifications under the Legal Metrology Act, 2009
    and Legal Metrology (Packaged Commodities) Rules, 2011.
    """
    return rule_engine.get_all_rules_metadata()
