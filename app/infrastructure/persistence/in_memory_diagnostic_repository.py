from collections import defaultdict
from app.domain.models.diagnostic_code import DiagnosticCode
from app.domain.value_objects.vehicle_id import VehicleId

class InMemoryDiagnosticRepository:
    def __init__(self):
        self._store: dict[str, dict[str, DiagnosticCode]] = defaultdict(dict)

    def save(self, code: DiagnosticCode) -> None:
        self._store[code.vehicle_id.value][code.code] = code

    def get_active(self, vehicle_id: VehicleId) -> list[DiagnosticCode]:
        return [c for c in self._store.get(vehicle_id.value, {}).values() if c.active]

    def get_by_code(self, vehicle_id: VehicleId, code: str) -> DiagnosticCode | None:
        return self._store.get(vehicle_id.value, {}).get(code)

    def clear(self, vehicle_id: VehicleId, code: str) -> bool:
        dc = self._store.get(vehicle_id.value, {}).get(code)
        if dc and dc.active:
            dc.active = False
            return True
        return False
