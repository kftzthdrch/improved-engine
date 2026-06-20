import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c

@pytest.fixture()
def client_with_telemetry(client):
    client.post("/vehicles/VH-001/telemetry", json={
        "speed_kph": 0, "battery_percent": 80, "odometer_km": 5000,
        "door_locked": True, "cabin_temperature_c": 22,
    })
    return client

def test_lock_succeeds_when_stopped(client_with_telemetry):
    r = client_with_telemetry.post("/vehicles/VH-001/commands/lock")
    assert r.status_code == 200
    assert r.json()["status"] == "SUCCEEDED"

def test_lock_rejected_when_moving(client):
    client.post("/vehicles/VH-001/telemetry", json={
        "speed_kph": 60, "battery_percent": 80, "odometer_km": 5000,
        "door_locked": True, "cabin_temperature_c": 22,
    })
    r = client.post("/vehicles/VH-001/commands/lock")
    assert r.status_code == 409

def test_unlock_succeeds(client_with_telemetry):
    r = client_with_telemetry.post("/vehicles/VH-001/commands/unlock")
    assert r.status_code == 200

def test_start_climate_rejected_when_battery_low(client):
    client.post("/vehicles/VH-001/telemetry", json={
        "speed_kph": 0, "battery_percent": 10, "odometer_km": 5000,
        "door_locked": True, "cabin_temperature_c": 22,
    })
    r = client.post("/vehicles/VH-001/commands/climate/start")
    assert r.status_code == 409

def test_set_temperature_out_of_range(client_with_telemetry):
    r = client_with_telemetry.post("/vehicles/VH-001/commands/climate/temperature", json={"target_celsius": 50})
    assert r.status_code == 409

def test_invalid_vehicle_id_returns_400():
    app = create_app()
    with TestClient(app) as c:
        r = c.post("/vehicles/%20/commands/lock")
        assert r.status_code == 400
