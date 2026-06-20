from dataclasses import dataclass, field
from datetime import datetime
from app.domain.enums import CommandType, CommandStatus
from app.domain.value_objects.vehicle_id import VehicleId
from app.domain.value_objects.command_id import CommandId

@dataclass
class Command:
    id: CommandId
    vehicle_id: VehicleId
    command_type: CommandType
    status: CommandStatus
    created_at: datetime
    updated_at: datetime
    payload: dict = field(default_factory=dict)
    failure_reason: str | None = None

    def mark_sent(self, updated_at: datetime) -> None:
        self.status = CommandStatus.SENT
        self.updated_at = updated_at

    def mark_succeeded(self, updated_at: datetime) -> None:
        self.status = CommandStatus.SUCCEEDED
        self.updated_at = updated_at

    def mark_failed(self, reason: str, updated_at: datetime) -> None:
        self.status = CommandStatus.FAILED
        self.failure_reason = reason
        self.updated_at = updated_at

    def mark_rejected(self, reason: str, updated_at: datetime) -> None:
        self.status = CommandStatus.REJECTED
        self.failure_reason = reason
        self.updated_at = updated_at
