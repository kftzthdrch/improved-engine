from dataclasses import dataclass
from datetime import datetime
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass(frozen=True)
class TelemetrySnapshot:
    vehicle_id: VehicleId
    speed_kph: float
    battery_percent: float
    odometer_km: float
    door_locked: bool
    cabin_temperature_c: float
    timestamp: datetime
