import pytest
from app.domain.value_objects.vehicle_id import VehicleId
from app.domain.value_objects.speed import Speed
from app.domain.value_objects.battery_percent import BatteryPercent
from app.domain.value_objects.temperature import Temperature
from app.domain.value_objects.odometer import Odometer
from app.domain.errors import InvalidVehicleIdError, InvalidCommandError


def test_vehicle_id_normalizes_to_uppercase():
    vid = VehicleId("vh-001")
    assert vid.value == "VH-001"

def test_vehicle_id_rejects_empty():
    with pytest.raises(InvalidVehicleIdError):
        VehicleId("")

def test_speed_rejects_negative():
    with pytest.raises(InvalidCommandError):
        Speed(-1)

def test_battery_rejects_over_100():
    with pytest.raises(InvalidCommandError):
        BatteryPercent(101)

def test_battery_rejects_negative():
    with pytest.raises(InvalidCommandError):
        BatteryPercent(-1)

def test_temperature_rejects_extreme():
    with pytest.raises(InvalidCommandError):
        Temperature(200)

def test_odometer_rejects_negative():
    with pytest.raises(InvalidCommandError):
        Odometer(-1)
