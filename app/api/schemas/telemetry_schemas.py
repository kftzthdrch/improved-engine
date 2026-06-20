from pydantic import BaseModel
from datetime import datetime

class TelemetryIngestRequest(BaseModel):
    speed_kph: float
    battery_percent: float
    odometer_km: float
    door_locked: bool
    cabin_temperature_c: float

class TelemetryResponse(BaseModel):
    vehicle_id: str
    speed_kph: float
    battery_percent: float
    odometer_km: float
    door_locked: bool
    cabin_temperature_c: float
    timestamp: datetime

class VehicleStatusResponse(BaseModel):
    vehicle_id: str
    speed_kph: float
    battery_percent: float
    odometer_km: float
    door_locked: bool
    cabin_temperature_c: float
    timestamp: datetime
