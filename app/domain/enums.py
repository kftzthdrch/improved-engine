from enum import Enum

class CommandType(str, Enum):
    LOCK = "LOCK"
    UNLOCK = "UNLOCK"
    START_CLIMATE = "START_CLIMATE"
    STOP_CLIMATE = "STOP_CLIMATE"
    SET_CABIN_TEMPERATURE = "SET_CABIN_TEMPERATURE"
    FLASH_LIGHTS = "FLASH_LIGHTS"
    HONK_HORN = "HONK_HORN"
    OPEN_TRUNK = "OPEN_TRUNK"
    CLOSE_WINDOWS = "CLOSE_WINDOWS"

class CommandStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"

class AlertType(str, Enum):
    LOW_BATTERY = "LOW_BATTERY"
    CABIN_OVERHEAT = "CABIN_OVERHEAT"
    VEHICLE_MOVING = "VEHICLE_MOVING"
    DOOR_UNLOCKED = "DOOR_UNLOCKED"
    STALE_TELEMETRY = "STALE_TELEMETRY"

class TripStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"

class DiagnosticSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ClimateState(str, Enum):
    ON = "ON"
    OFF = "OFF"
