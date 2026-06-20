from dataclasses import dataclass
from app.application.ports.telemetry_repository import TelemetryRepository
from app.domain.errors import TelemetryNotFoundError
from app.domain.models.telemetry import TelemetrySnapshot
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class GetVehicleStatusUseCase:
    telemetry_repo: TelemetryRepository

    def execute(self, vehicle_id: VehicleId) -> TelemetrySnapshot:
        snapshot = self.telemetry_repo.get_latest(vehicle_id)
        if snapshot is None:
            raise TelemetryNotFoundError(f"No telemetry found for vehicle {vehicle_id.value}")
        return snapshot
