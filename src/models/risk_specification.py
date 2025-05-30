from typing import Optional
from pydantic import BaseModel

class RiskSpecification(BaseModel):
    cpe: Optional[str] = None
    risk_score: Optional[float] = None
    privacy_score: Optional[float] = None
