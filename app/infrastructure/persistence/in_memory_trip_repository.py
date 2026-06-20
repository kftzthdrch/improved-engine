from app.domain.models.trip import TripSession
from app.domain.enums import TripStatus
from app.domain.value_objects.vehicle_id import VehicleId
from app.domain.value_objects.trip_id import TripId

class InMemoryTripRepository:
    def __init__(self):
        self._store: dict[str, TripSession] = {}

    def save(self, trip: TripSession) -> None:
        self._store[trip.id.value] = trip

    def get(self, trip_id: TripId) -> TripSession | None:
        return self._store.get(trip_id.value)

    def get_active(self, vehicle_id: VehicleId) -> TripSession | None:
        for trip in self._store.values():
            if trip.vehicle_id.value == vehicle_id.value and trip.status == TripStatus.ACTIVE:
                return trip
        return None

    def get_latest_completed(self, vehicle_id: VehicleId) -> TripSession | None:
        completed = [
            t for t in self._store.values()
            if t.vehicle_id.value == vehicle_id.value and t.status == TripStatus.COMPLETED
        ]
        return max(completed, key=lambda t: t.ended_at) if completed else None
