from fastapi import APIRouter, Depends, Path
from app.api.dependencies import (
    get_lock_vehicle_use_case, get_unlock_vehicle_use_case, get_start_climate_use_case,
    get_stop_climate_use_case, get_set_cabin_temperature_use_case, get_flash_lights_use_case,
    get_honk_horn_use_case, get_open_trunk_use_case, get_close_windows_use_case,
    get_command_by_id_use_case,
)
from app.api.schemas.command_schemas import CommandResponse, SetCabinTemperatureRequest, HonkHornRequest
from app.domain.errors import CommandNotFoundError
from app.domain.value_objects.vehicle_id import VehicleId
from app.domain.value_objects.command_id import CommandId

router = APIRouter(tags=["commands"])

def _to_response(cmd) -> CommandResponse:
    return CommandResponse(
        id=cmd.id.value,
        vehicle_id=cmd.vehicle_id.value,
        command_type=cmd.command_type.value,
        status=cmd.status.value,
        created_at=cmd.created_at,
        updated_at=cmd.updated_at,
        payload=cmd.payload,
        failure_reason=cmd.failure_reason,
    )

@router.post("/vehicles/{vehicle_id}/commands/lock", response_model=CommandResponse, status_code=200)
def lock_vehicle(vehicle_id: str = Path(...), use_case=Depends(get_lock_vehicle_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id))
    return _to_response(cmd)

@router.post("/vehicles/{vehicle_id}/commands/unlock", response_model=CommandResponse, status_code=200)
def unlock_vehicle(vehicle_id: str = Path(...), use_case=Depends(get_unlock_vehicle_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id))
    return _to_response(cmd)

@router.post("/vehicles/{vehicle_id}/commands/climate/start", response_model=CommandResponse, status_code=200)
def start_climate(vehicle_id: str = Path(...), use_case=Depends(get_start_climate_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id))
    return _to_response(cmd)

@router.post("/vehicles/{vehicle_id}/commands/climate/stop", response_model=CommandResponse, status_code=200)
def stop_climate(vehicle_id: str = Path(...), use_case=Depends(get_stop_climate_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id))
    return _to_response(cmd)

@router.post("/vehicles/{vehicle_id}/commands/climate/temperature", response_model=CommandResponse, status_code=200)
def set_cabin_temperature(body: SetCabinTemperatureRequest, vehicle_id: str = Path(...), use_case=Depends(get_set_cabin_temperature_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id), body.target_celsius)
    return _to_response(cmd)

@router.post("/vehicles/{vehicle_id}/commands/lights/flash", response_model=CommandResponse, status_code=200)
def flash_lights(vehicle_id: str = Path(...), use_case=Depends(get_flash_lights_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id))
    return _to_response(cmd)

@router.post("/vehicles/{vehicle_id}/commands/horn", response_model=CommandResponse, status_code=200)
def honk_horn(body: HonkHornRequest = None, vehicle_id: str = Path(...), use_case=Depends(get_honk_horn_use_case)):
    quiet = body.quiet_mode if body else False
    cmd = use_case.execute(VehicleId(vehicle_id), quiet)
    return _to_response(cmd)

@router.post("/vehicles/{vehicle_id}/commands/trunk/open", response_model=CommandResponse, status_code=200)
def open_trunk(vehicle_id: str = Path(...), use_case=Depends(get_open_trunk_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id))
    return _to_response(cmd)

@router.post("/vehicles/{vehicle_id}/commands/windows/close", response_model=CommandResponse, status_code=200)
def close_windows(vehicle_id: str = Path(...), use_case=Depends(get_close_windows_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id))
    return _to_response(cmd)

@router.get("/commands/{command_id}", response_model=CommandResponse)
def get_command(command_id: str = Path(...), repo=Depends(get_command_by_id_use_case)):
    cmd = repo.get(CommandId(command_id))
    if cmd is None:
        raise CommandNotFoundError(f"Command {command_id} not found")
    return _to_response(cmd)
