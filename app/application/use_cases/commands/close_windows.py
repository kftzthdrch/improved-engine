from dataclasses import dataclass
from app.application.ports.command_repository import CommandRepository
from app.application.ports.vehicle_command_gateway import VehicleCommandGateway
from app.application.ports.clock import Clock
from app.application.ports.id_generator import IdGenerator
from app.domain.enums import CommandType, CommandStatus
from app.domain.models.command import Command
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class CloseWindowsUseCase:
    command_repo: CommandRepository
    gateway: VehicleCommandGateway
    clock: Clock
    id_gen: IdGenerator

    def execute(self, vehicle_id: VehicleId) -> Command:
        now = self.clock.now()
        command = Command(
            id=self.id_gen.new_command_id(),
            vehicle_id=vehicle_id,
            command_type=CommandType.CLOSE_WINDOWS,
            status=CommandStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        self.command_repo.save(command)
        result = self.gateway.send(vehicle_id, command.id, command.command_type, {})
        if result.success:
            command.mark_succeeded(self.clock.now())
        else:
            command.mark_failed(result.error_message or "Gateway failure", self.clock.now())
        self.command_repo.save(command)
        return command
