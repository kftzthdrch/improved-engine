from dataclasses import dataclass
from app.application.ports.diagnostic_repository import DiagnosticRepository
from app.application.ports.clock import Clock
from app.domain.enums import DiagnosticSeverity
from app.domain.models.diagnostic_code import DiagnosticCode
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class DiagnosticCodeInput:
    code: str
    severity: DiagnosticSeverity
    description: str

@dataclass
class IngestDiagnosticCodesUseCase:
    diagnostic_repo: DiagnosticRepository
    clock: Clock

    def execute(self, vehicle_id: VehicleId, codes: list[DiagnosticCodeInput]) -> list[DiagnosticCode]:
        now = self.clock.now()
        results = []
        for item in codes:
            existing = self.diagnostic_repo.get_by_code(vehicle_id, item.code)
            if existing:
                existing.last_seen_at = now
                existing.active = True
                self.diagnostic_repo.save(existing)
                results.append(existing)
            else:
                dc = DiagnosticCode(
                    vehicle_id=vehicle_id,
                    code=item.code,
                    severity=item.severity,
                    description=item.description,
                    first_seen_at=now,
                    last_seen_at=now,
                    active=True,
                )
                self.diagnostic_repo.save(dc)
                results.append(dc)
        return results
