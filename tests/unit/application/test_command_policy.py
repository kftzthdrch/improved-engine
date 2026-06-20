import pytest
from datetime import datetime, timezone
from app.application.services.command_policy import CommandPolicy
from app.domain.errors import CommandRejectedError
from app.domain.models.telemetry import TelemetrySnapshot
from app.domain.value_objects.vehicle_id import VehicleId

def make_snapshot(speed=0.0, battery=80.0):
    return TelemetrySnapshot(
        vehicle_id=VehicleId("VH-001"),
        speed_kph=speed,
        battery_percent=battery,
        odometer_km=1000,
        door_locked=True,
        cabin_temperature_c=22.0,
        timestamp=datetime.now(timezone.utc),
    )

policy = CommandPolicy()

def test_enforce_not_moving_passes_when_stopped():
    policy.enforce_not_moving(make_snapshot(speed=0))

def test_enforce_not_moving_raises_when_moving():
    with pytest.raises(CommandRejectedError):
        policy.enforce_not_moving(make_snapshot(speed=10))

def test_enforce_battery_raises_when_low():
    with pytest.raises(CommandRejectedError):
        policy.enforce_battery_sufficient(make_snapshot(battery=10))

def test_enforce_battery_passes_when_ok():
    policy.enforce_battery_sufficient(make_snapshot(battery=50))

def test_enforce_temperature_range():
    policy.enforce_cabin_temperature_range(22)
    with pytest.raises(CommandRejectedError):
        policy.enforce_cabin_temperature_range(5)
    with pytest.raises(CommandRejectedError):
        policy.enforce_cabin_temperature_range(35)

def test_enforce_quiet_mode():
    policy.enforce_quiet_mode_off(False)
    with pytest.raises(CommandRejectedError):
        policy.enforce_quiet_mode_off(True)
