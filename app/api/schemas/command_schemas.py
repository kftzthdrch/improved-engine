from pydantic import BaseModel
from datetime import datetime

class SetCabinTemperatureRequest(BaseModel):
    target_celsius: float

class HonkHornRequest(BaseModel):
    quiet_mode: bool = False

class CommandResponse(BaseModel):
    id: str
    vehicle_id: str
    command_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    payload: dict = {}
    failure_reason: str | None = None
