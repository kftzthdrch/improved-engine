from dataclasses import dataclass
from datetime import datetime
from app.domain.enums import TripStatus
from app.domain.value_objects.vehicle_id import VehicleId
from app.domain.value_objects.trip_id import TripId

@dataclass
class TripSession:
    id: TripId
    vehicle_id: VehicleId
    status: TripStatus
    started_at: datetime
    start_odometer_km: float
    ended_at: datetime | None = None
    end_odometer_km: float | None = None

    @property
    def distance_km(self) -> float | None:
        if self.end_odometer_km is not None:
            return self.end_odometer_km - self.start_odometer_km
        return None
