from app.domain.models.maintenance import MaintenanceState
from app.domain.value_objects.vehicle_id import VehicleId

class InMemoryMaintenanceRepository:
    def __init__(self):
        self._store: dict[str, MaintenanceState] = {}

    def get_or_create(self, vehicle_id: VehicleId) -> MaintenanceState:
        if vehicle_id.value not in self._store:
            self._store[vehicle_id.value] = MaintenanceState(vehicle_id=vehicle_id)
        return self._store[vehicle_id.value]

    def save(self, state: MaintenanceState) -> None:
        self._store[state.vehicle_id.value] = state
