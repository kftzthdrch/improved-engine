from dataclasses import dataclass
from app.application.ports.telemetry_repository import TelemetryRepository
from app.application.ports.clock import Clock
from app.application.services.telemetry_validation import TelemetryValidation
from app.domain.models.telemetry import TelemetrySnapshot
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class IngestTelemetryUseCase:
    telemetry_repo: TelemetryRepository
    clock: Clock
    validation: TelemetryValidation

    def execute(self, vehicle_id: VehicleId, speed_kph: float, battery_percent: float,
                odometer_km: float, door_locked: bool, cabin_temperature_c: float) -> TelemetrySnapshot:
        self.validation.validate(speed_kph, battery_percent, odometer_km, cabin_temperature_c)
        snapshot = TelemetrySnapshot(
            vehicle_id=vehicle_id,
            speed_kph=speed_kph,
            battery_percent=battery_percent,
            odometer_km=odometer_km,
            door_locked=door_locked,
            cabin_temperature_c=cabin_temperature_c,
            timestamp=self.clock.now(),
        )
        self.telemetry_repo.save(snapshot)
        return snapshot
