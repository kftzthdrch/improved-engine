import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c

def test_ingest_telemetry(client):
    r = client.post("/vehicles/VH-001/telemetry", json={
        "speed_kph": 50, "battery_percent": 60, "odometer_km": 10000,
        "door_locked": True, "cabin_temperature_c": 21,
    })
    assert r.status_code == 201
    assert r.json()["speed_kph"] == 50

def test_get_status(client):
    client.post("/vehicles/VH-001/telemetry", json={
        "speed_kph": 0, "battery_percent": 80, "odometer_km": 5000,
        "door_locked": True, "cabin_temperature_c": 22,
    })
    r = client.get("/vehicles/VH-001/status")
    assert r.status_code == 200
    assert r.json()["vehicle_id"] == "VH-001"

def test_status_not_found(client):
    r = client.get("/vehicles/VH-UNKNOWN/status")
    assert r.status_code == 404

def test_telemetry_history(client):
    for i in range(3):
        client.post("/vehicles/VH-001/telemetry", json={
            "speed_kph": i, "battery_percent": 80, "odometer_km": 5000 + i,
            "door_locked": True, "cabin_temperature_c": 22,
        })
    r = client.get("/vehicles/VH-001/telemetry/history")
    assert r.status_code == 200
    assert len(r.json()) == 3
