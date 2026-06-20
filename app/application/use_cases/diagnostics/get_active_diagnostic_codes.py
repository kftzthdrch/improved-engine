from dataclasses import dataclass
from app.application.ports.diagnostic_repository import DiagnosticRepository
from app.domain.models.diagnostic_code import DiagnosticCode
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class GetActiveDiagnosticCodesUseCase:
    diagnostic_repo: DiagnosticRepository

    def execute(self, vehicle_id: VehicleId) -> list[DiagnosticCode]:
        return self.diagnostic_repo.get_active(vehicle_id)
