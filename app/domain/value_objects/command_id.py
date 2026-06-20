from dataclasses import dataclass

@dataclass(frozen=True)
class CommandId:
    value: str
