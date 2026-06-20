from fastapi.testclient import TestClient
from app.main import create_app
from app.api.dependencies import get_lock_vehicle_use_case
from app.domain.enums import CommandType, CommandStatus
from app.domain.models.command import Command
from app.domain.value_objects.vehicle_id import VehicleId
from app.domain.value_objects.command_id import CommandId
from datetime import datetime, timezone

def make_stub_command():
    return Command(
        id=CommandId("stub-id"),
        vehicle_id=VehicleId("VH-TEST"),
        command_type=CommandType.LOCK,
        status=CommandStatus.SUCCEEDED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

def test_dependency_override():
    app = create_app()

    class StubLockUseCase:
        def execute(self, vehicle_id):
            return make_stub_command()

    app.dependency_overrides[get_lock_vehicle_use_case] = lambda: StubLockUseCase()
    with TestClient(app) as client:
        r = client.post("/vehicles/VH-TEST/commands/lock")
    assert r.status_code == 200
    assert r.json()["id"] == "stub-id"
    assert r.json()["status"] == "SUCCEEDED"
