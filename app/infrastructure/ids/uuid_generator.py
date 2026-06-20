import uuid
from app.domain.value_objects.command_id import CommandId
from app.domain.value_objects.trip_id import TripId

class UuidGenerator:
    def new_command_id(self) -> CommandId:
        return CommandId(value=str(uuid.uuid4()))

    def new_trip_id(self) -> TripId:
        return TripId(value=str(uuid.uuid4()))
