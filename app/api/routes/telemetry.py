from fastapi import APIRouter, Depends, Path
from app.api.dependencies import (
    get_ingest_telemetry_use_case, get_vehicle_status_use_case, get_telemetry_history_use_case,
)
from app.api.schemas.telemetry_schemas import TelemetryIngestRequest, TelemetryResponse, VehicleStatusResponse
from app.domain.value_objects.vehicle_id import VehicleId

router = APIRouter(tags=["telemetry"])

def _to_telemetry_response(snap) -> TelemetryResponse:
    return TelemetryResponse(
        vehicle_id=snap.vehicle_id.value,
        speed_kph=snap.speed_kph,
        battery_percent=snap.battery_percent,
        odometer_km=snap.odometer_km,
        door_locked=snap.door_locked,
        cabin_temperature_c=snap.cabin_temperature_c,
        timestamp=snap.timestamp,
    )

@router.post("/vehicles/{vehicle_id}/telemetry", response_model=TelemetryResponse, status_code=201)
def ingest_telemetry(body: TelemetryIngestRequest, vehicle_id: str = Path(...), use_case=Depends(get_ingest_telemetry_use_case)):
    snap = use_case.execute(
        VehicleId(vehicle_id), body.speed_kph, body.battery_percent,
        body.odometer_km, body.door_locked, body.cabin_temperature_c,
    )
    return _to_telemetry_response(snap)

@router.get("/vehicles/{vehicle_id}/status", response_model=VehicleStatusResponse)
def get_vehicle_status(vehicle_id: str = Path(...), use_case=Depends(get_vehicle_status_use_case)):
    snap = use_case.execute(VehicleId(vehicle_id))
    return VehicleStatusResponse(
        vehicle_id=snap.vehicle_id.value,
        speed_kph=snap.speed_kph,
        battery_percent=snap.battery_percent,
        odometer_km=snap.odometer_km,
        door_locked=snap.door_locked,
        cabin_temperature_c=snap.cabin_temperature_c,
        timestamp=snap.timestamp,
    )

@router.get("/vehicles/{vehicle_id}/telemetry/history", response_model=list[TelemetryResponse])
def get_telemetry_history(vehicle_id: str = Path(...), use_case=Depends(get_telemetry_history_use_case)):
    history = use_case.execute(VehicleId(vehicle_id))
    return [_to_telemetry_response(s) for s in history]
