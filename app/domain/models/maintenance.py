from dataclasses import dataclass
from datetime import datetime
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class MaintenanceState:
    vehicle_id: VehicleId
    last_service_odometer_km: float = 0.0
    last_tire_check_odometer_km: float = 0.0
    last_service_date: datetime | None = None
    last_tire_check_date: datetime | None = None

    SERVICE_INTERVAL_KM = 15000
    TIRE_CHECK_INTERVAL_KM = 10000

    def is_service_due(self, current_odometer_km: float) -> bool:
        return (current_odometer_km - self.last_service_odometer_km) >= self.SERVICE_INTERVAL_KM

    def is_tire_check_due(self, current_odometer_km: float) -> bool:
        return (current_odometer_km - self.last_tire_check_odometer_km) >= self.TIRE_CHECK_INTERVAL_KM
