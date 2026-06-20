from pydantic import BaseModel

class CommandEligibilityItem(BaseModel):
    command_type: str
    allowed: bool
    reason: str | None = None

class CommandEligibilityResponse(BaseModel):
    vehicle_id: str
    eligibility: list[CommandEligibilityItem]
