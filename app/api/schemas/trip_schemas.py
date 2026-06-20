from pydantic import BaseModel
from datetime import datetime

class TripResponse(BaseModel):
    id: str
    vehicle_id: str
    status: str
    started_at: datetime
    start_odometer_km: float
    ended_at: datetime | None = None
    end_odometer_km: float | None = None

class TripSummaryResponse(BaseModel):
    id: str
    vehicle_id: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    start_odometer_km: float
    end_odometer_km: float | None = None
    distance_km: float | None = None
