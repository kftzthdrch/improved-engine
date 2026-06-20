from dataclasses import dataclass
from app.application.ports.trip_repository import TripRepository
from app.application.ports.telemetry_repository import TelemetryRepository
from app.application.ports.clock import Clock
from app.domain.enums import TripStatus
from app.domain.errors import TripNotFoundError, TelemetryNotFoundError
from app.domain.models.trip import TripSession
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class EndTripUseCase:
    trip_repo: TripRepository
    telemetry_repo: TelemetryRepository
    clock: Clock

    def execute(self, vehicle_id: VehicleId) -> TripSession:
        trip = self.trip_repo.get_active(vehicle_id)
        if trip is None:
            raise TripNotFoundError("No active trip found")
        latest = self.telemetry_repo.get_latest(vehicle_id)
        if latest is None:
            raise TelemetryNotFoundError("No telemetry for trip end")
        trip.status = TripStatus.COMPLETED
        trip.ended_at = self.clock.now()
        trip.end_odometer_km = latest.odometer_km
        self.trip_repo.save(trip)
        return trip
