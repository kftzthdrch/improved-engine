from pydantic import BaseModel
from datetime import datetime

class AlertResponse(BaseModel):
    vehicle_id: str
    alert_type: str
    message: str
    triggered_at: datetime
    active: bool
