from pydantic import BaseModel
from datetime import datetime

class DiagnosticCodeInput(BaseModel):
    code: str
    severity: str
    description: str

class DiagnosticCodeRequest(BaseModel):
    codes: list[DiagnosticCodeInput]

class DiagnosticCodeResponse(BaseModel):
    vehicle_id: str
    code: str
    severity: str
    description: str
    first_seen_at: datetime
    last_seen_at: datetime
    active: bool
