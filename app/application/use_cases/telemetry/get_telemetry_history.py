from dataclasses import dataclass
from app.application.ports.telemetry_repository import TelemetryRepository
from app.domain.models.telemetry import TelemetrySnapshot
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class GetTelemetryHistoryUseCase:
    telemetry_repo: TelemetryRepository

    def execute(self, vehicle_id: VehicleId) -> list[TelemetrySnapshot]:
        return self.telemetry_repo.get_history(vehicle_id)
