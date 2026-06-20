from collections import defaultdict
from app.domain.models.telemetry import TelemetrySnapshot
from app.domain.value_objects.vehicle_id import VehicleId

MAX_HISTORY = 20

class InMemoryTelemetryRepository:
    def __init__(self):
        self._store: dict[str, list[TelemetrySnapshot]] = defaultdict(list)

    def save(self, snapshot: TelemetrySnapshot) -> None:
        history = self._store[snapshot.vehicle_id.value]
        history.append(snapshot)
        if len(history) > MAX_HISTORY:
            self._store[snapshot.vehicle_id.value] = history[-MAX_HISTORY:]

    def get_latest(self, vehicle_id: VehicleId) -> TelemetrySnapshot | None:
        history = self._store.get(vehicle_id.value, [])
        return history[-1] if history else None

    def get_history(self, vehicle_id: VehicleId) -> list[TelemetrySnapshot]:
        return list(self._store.get(vehicle_id.value, []))
