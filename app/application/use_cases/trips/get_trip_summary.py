from dataclasses import dataclass
from app.application.ports.trip_repository import TripRepository
from app.domain.errors import TripNotFoundError
from app.domain.models.trip import TripSession
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class GetTripSummaryUseCase:
    trip_repo: TripRepository

    def execute(self, vehicle_id: VehicleId) -> TripSession:
        trip = self.trip_repo.get_latest_completed(vehicle_id)
        if trip is None:
            raise TripNotFoundError("No completed trips found")
        return trip
