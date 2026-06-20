class DomainError(Exception):
    pass

class InvalidVehicleIdError(DomainError):
    pass

class InvalidCommandError(DomainError):
    pass

class CommandRejectedError(DomainError):
    pass

class CommandNotFoundError(DomainError):
    pass

class TelemetryNotFoundError(DomainError):
    pass

class TripAlreadyActiveError(DomainError):
    pass

class TripNotFoundError(DomainError):
    pass

class DiagnosticCodeNotFoundError(DomainError):
    pass

class AlertNotFoundError(DomainError):
    pass
