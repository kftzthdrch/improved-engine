from app.domain.models.command import Command
from app.domain.value_objects.command_id import CommandId
from app.domain.value_objects.vehicle_id import VehicleId

class InMemoryCommandRepository:
    def __init__(self):
        self._store: dict[str, Command] = {}

    def save(self, command: Command) -> None:
        self._store[command.id.value] = command

    def get(self, command_id: CommandId) -> Command | None:
        return self._store.get(command_id.value)

    def list_for_vehicle(self, vehicle_id: VehicleId) -> list[Command]:
        return [c for c in self._store.values() if c.vehicle_id.value == vehicle_id.value]
