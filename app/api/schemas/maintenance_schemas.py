from pydantic import BaseModel
from datetime import datetime

class MaintenanceStatusResponse(BaseModel):
    vehicle_id: str
    last_service_odometer_km: float
    last_tire_check_odometer_km: float
    last_service_date: datetime | None = None
    last_tire_check_date: datetime | None = None
    current_odometer_km: float
    service_due: bool
    tire_check_due: bool
