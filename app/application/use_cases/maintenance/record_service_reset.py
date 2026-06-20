from dataclasses import dataclass
from app.application.ports.maintenance_repository import MaintenanceRepository
from app.application.ports.telemetry_repository import TelemetryRepository
from app.application.ports.clock import Clock
from app.domain.models.maintenance import MaintenanceState
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class RecordServiceResetUseCase:
    maintenance_repo: MaintenanceRepository
    telemetry_repo: TelemetryRepository
    clock: Clock

    def execute(self, vehicle_id: VehicleId) -> MaintenanceState:
        state = self.maintenance_repo.get_or_create(vehicle_id)
        latest = self.telemetry_repo.get_latest(vehicle_id)
        now = self.clock.now()
        state.last_service_odometer_km = latest.odometer_km if latest else state.last_service_odometer_km
        state.last_service_date = now
        state.last_tire_check_odometer_km = latest.odometer_km if latest else state.last_tire_check_odometer_km
        state.last_tire_check_date = now
        self.maintenance_repo.save(state)
        return state
