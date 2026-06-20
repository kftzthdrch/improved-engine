from dataclasses import dataclass
from app.application.ports.command_repository import CommandRepository
from app.application.ports.vehicle_command_gateway import VehicleCommandGateway
from app.application.ports.clock import Clock
from app.application.ports.id_generator import IdGenerator
from app.application.services.command_policy import CommandPolicy
from app.domain.enums import CommandType, CommandStatus
from app.domain.models.command import Command
from app.domain.value_objects.vehicle_id import VehicleId

@dataclass
class HonkHornUseCase:
    command_repo: CommandRepository
    gateway: VehicleCommandGateway
    clock: Clock
    id_gen: IdGenerator
    policy: CommandPolicy

    def execute(self, vehicle_id: VehicleId, quiet_mode: bool) -> Command:
        now = self.clock.now()
        command = Command(
            id=self.id_gen.new_command_id(),
            vehicle_id=vehicle_id,
            command_type=CommandType.HONK_HORN,
            status=CommandStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        try:
            self.policy.enforce_quiet_mode_off(quiet_mode)
        except Exception as e:
            command.mark_rejected(str(e), self.clock.now())
            self.command_repo.save(command)
            raise
        self.command_repo.save(command)
        result = self.gateway.send(vehicle_id, command.id, command.command_type, {})
        if result.success:
            command.mark_succeeded(self.clock.now())
        else:
            command.mark_failed(result.error_message or "Gateway failure", self.clock.now())
        self.command_repo.save(command)
        return command
