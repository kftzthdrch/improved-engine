from typing import Protocol
from app.domain.enums import CommandType
from app.domain.value_objects.vehicle_id import VehicleId
from app.domain.value_objects.command_id import CommandId

class GatewayResult:
    def __init__(self, success: bool, error_message: str | None = None):
        self.success = success
        self.error_message = error_message

class VehicleCommandGateway(Protocol):
    def send(self, vehicle_id: VehicleId, command_id: CommandId, command_type: CommandType, payload: dict) -> GatewayResult: ...
