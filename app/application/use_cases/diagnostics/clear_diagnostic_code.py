from dataclasses import dataclass
from app.application.ports.diagnostic_repository import DiagnosticRepository
from app.domain.errors import DiagnosticCodeNotFoundError
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class ClearDiagnosticCodeUseCase:
    diagnostic_repo: DiagnosticRepository

    def execute(self, vehicle_id: VehicleId, code: str) -> None:
        cleared = self.diagnostic_repo.clear(vehicle_id, code)
        if not cleared:
            raise DiagnosticCodeNotFoundError(f"No active diagnostic code: {code}")
