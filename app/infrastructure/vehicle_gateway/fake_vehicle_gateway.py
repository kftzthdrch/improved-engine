from app.application.ports.vehicle_command_gateway import GatewayResult
from app.domain.enums import CommandType
from app.domain.value_objects.vehicle_id import VehicleId
from app.domain.value_objects.command_id import CommandId

class FakeVehicleCommandGateway:
    def __init__(self, should_fail: bool = False, fail_reason: str = "Simulated gateway failure"):
        self._should_fail = should_fail
        self._fail_reason = fail_reason
        self.sent_commands: list[dict] = []

    def send(self, vehicle_id: VehicleId, command_id: CommandId, command_type: CommandType, payload: dict) -> GatewayResult:
        self.sent_commands.append({
            "vehicle_id": vehicle_id.value,
            "command_id": command_id.value,
            "command_type": command_type.value,
            "payload": payload,
        })
        if self._should_fail:
            return GatewayResult(success=False, error_message=self._fail_reason)
        return GatewayResult(success=True)
