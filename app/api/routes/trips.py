from fastapi import APIRouter, Depends, Path
from app.api.dependencies import (
    get_start_trip_use_case, get_end_trip_use_case,
    get_current_trip_use_case, get_trip_summary_use_case,
)
from app.api.schemas.trip_schemas import TripResponse, TripSummaryResponse
from app.domain.value_objects.vehicle_id import VehicleId

router = APIRouter(tags=["trips"])

def _to_trip_response(trip) -> TripResponse:
    return TripResponse(
        id=trip.id.value,
        vehicle_id=trip.vehicle_id.value,
        status=trip.status.value,
        started_at=trip.started_at,
        start_odometer_km=trip.start_odometer_km,
        ended_at=trip.ended_at,
        end_odometer_km=trip.end_odometer_km,
    )

@router.post("/vehicles/{vehicle_id}/trips/start", response_model=TripResponse, status_code=201)
def start_trip(vehicle_id: str = Path(...), use_case=Depends(get_start_trip_use_case)):
    trip = use_case.execute(VehicleId(vehicle_id))
    return _to_trip_response(trip)

@router.post("/vehicles/{vehicle_id}/trips/end", response_model=TripResponse, status_code=200)
def end_trip(vehicle_id: str = Path(...), use_case=Depends(get_end_trip_use_case)):
    trip = use_case.execute(VehicleId(vehicle_id))
    return _to_trip_response(trip)

@router.get("/vehicles/{vehicle_id}/trips/current", response_model=TripResponse)
def get_current_trip(vehicle_id: str = Path(...), use_case=Depends(get_current_trip_use_case)):
    trip = use_case.execute(VehicleId(vehicle_id))
    return _to_trip_response(trip)

@router.get("/vehicles/{vehicle_id}/trips/latest-summary", response_model=TripSummaryResponse)
def get_trip_summary(vehicle_id: str = Path(...), use_case=Depends(get_trip_summary_use_case)):
    trip = use_case.execute(VehicleId(vehicle_id))
    return TripSummaryResponse(
        id=trip.id.value,
        vehicle_id=trip.vehicle_id.value,
        status=trip.status.value,
        started_at=trip.started_at,
        ended_at=trip.ended_at,
        start_odometer_km=trip.start_odometer_km,
        end_odometer_km=trip.end_odometer_km,
        distance_km=trip.distance_km,
    )
