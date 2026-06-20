from dataclasses import dataclass
from app.application.ports.maintenance_repository import MaintenanceRepository
from app.application.ports.telemetry_repository import TelemetryRepository
from app.application.services.maintenance_rules import MaintenanceRules
from app.domain.models.maintenance import MaintenanceState
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class MaintenanceStatus:
    state: MaintenanceState
    current_odometer_km: float
    service_due: bool
    tire_check_due: bool

@dataclass
class GetMaintenanceStatusUseCase:
    maintenance_repo: MaintenanceRepository
    telemetry_repo: TelemetryRepository
    rules: MaintenanceRules

    def execute(self, vehicle_id: VehicleId) -> MaintenanceStatus:
        state = self.maintenance_repo.get_or_create(vehicle_id)
        latest = self.telemetry_repo.get_latest(vehicle_id)
        current_km = latest.odometer_km if latest else 0.0
        return MaintenanceStatus(
            state=state,
            current_odometer_km=current_km,
            service_due=self.rules.check_service_due(state, current_km),
            tire_check_due=self.rules.check_tire_check_due(state, current_km),
        )
