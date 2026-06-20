from typing import Protocol
from app.domain.value_objects.command_id import CommandId
from app.domain.value_objects.trip_id import TripId

class IdGenerator(Protocol):
    def new_command_id(self) -> CommandId: ...
    def new_trip_id(self) -> TripId: ...
