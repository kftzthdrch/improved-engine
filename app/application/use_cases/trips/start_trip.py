from dataclasses import dataclass
from app.application.ports.trip_repository import TripRepository
from app.application.ports.telemetry_repository import TelemetryRepository
from app.application.ports.clock import Clock
from app.application.ports.id_generator import IdGenerator
from app.domain.enums import TripStatus
from app.domain.errors import TelemetryNotFoundError, TripAlreadyActiveError
from app.domain.models.trip import TripSession
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class StartTripUseCase:
    trip_repo: TripRepository
    telemetry_repo: TelemetryRepository
    clock: Clock
    id_gen: IdGenerator

    def execute(self, vehicle_id: VehicleId) -> TripSession:
        latest = self.telemetry_repo.get_latest(vehicle_id)
        if latest is None:
            raise TelemetryNotFoundError("No telemetry exists; cannot start trip")
        existing = self.trip_repo.get_active(vehicle_id)
        if existing is not None:
            raise TripAlreadyActiveError("A trip is already active for this vehicle")
        trip = TripSession(
            id=self.id_gen.new_trip_id(),
            vehicle_id=vehicle_id,
            status=TripStatus.ACTIVE,
            started_at=self.clock.now(),
            start_odometer_km=latest.odometer_km,
        )
        self.trip_repo.save(trip)
        return trip
