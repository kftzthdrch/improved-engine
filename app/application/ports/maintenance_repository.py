from typing import Protocol
from app.domain.models.maintenance import MaintenanceState
from app.domain.value_objects.vehicle_id import VehicleId

class MaintenanceRepository(Protocol):
    def get_or_create(self, vehicle_id: VehicleId) -> MaintenanceState: ...
    def save(self, state: MaintenanceState) -> None: ...
