from fastapi import Request
from app.composition.container import Container

def get_container(request: Request) -> Container:
    return request.app.state.container

def get_lock_vehicle_use_case(request: Request):
    return get_container(request).lock_vehicle

def get_unlock_vehicle_use_case(request: Request):
    return get_container(request).unlock_vehicle

def get_start_climate_use_case(request: Request):
    return get_container(request).start_climate

def get_stop_climate_use_case(request: Request):
    return get_container(request).stop_climate

def get_set_cabin_temperature_use_case(request: Request):
    return get_container(request).set_cabin_temperature

def get_flash_lights_use_case(request: Request):
    return get_container(request).flash_lights

def get_honk_horn_use_case(request: Request):
    return get_container(request).honk_horn

def get_open_trunk_use_case(request: Request):
    return get_container(request).open_trunk

def get_close_windows_use_case(request: Request):
    return get_container(request).close_windows

def get_ingest_telemetry_use_case(request: Request):
    return get_container(request).ingest_telemetry

def get_vehicle_status_use_case(request: Request):
    return get_container(request).get_vehicle_status

def get_telemetry_history_use_case(request: Request):
    return get_container(request).get_telemetry_history

def get_command_eligibility_use_case(request: Request):
    return get_container(request).get_command_eligibility

def get_evaluate_alerts_use_case(request: Request):
    return get_container(request).evaluate_vehicle_alerts

def get_active_alerts_use_case(request: Request):
    return get_container(request).get_active_alerts

def get_clear_alert_use_case(request: Request):
    return get_container(request).clear_vehicle_alert

def get_start_trip_use_case(request: Request):
    return get_container(request).start_trip

def get_end_trip_use_case(request: Request):
    return get_container(request).end_trip

def get_current_trip_use_case(request: Request):
    return get_container(request).get_current_trip

def get_trip_summary_use_case(request: Request):
    return get_container(request).get_trip_summary

def get_maintenance_status_use_case(request: Request):
    return get_container(request).get_maintenance_status

def get_service_reset_use_case(request: Request):
    return get_container(request).record_service_reset

def get_ingest_diagnostics_use_case(request: Request):
    return get_container(request).ingest_diagnostic_codes

def get_active_diagnostics_use_case(request: Request):
    return get_container(request).get_active_diagnostic_codes

def get_clear_diagnostic_use_case(request: Request):
    return get_container(request).clear_diagnostic_code

def get_command_by_id_use_case(request: Request):
    return get_container(request).command_repo
