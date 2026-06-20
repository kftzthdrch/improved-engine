from app.infrastructure.persistence.in_memory_command_repository import InMemoryCommandRepository
from app.infrastructure.persistence.in_memory_telemetry_repository import InMemoryTelemetryRepository
from app.infrastructure.persistence.in_memory_alert_repository import InMemoryAlertRepository
from app.infrastructure.persistence.in_memory_trip_repository import InMemoryTripRepository
from app.infrastructure.persistence.in_memory_maintenance_repository import InMemoryMaintenanceRepository
from app.infrastructure.persistence.in_memory_diagnostic_repository import InMemoryDiagnosticRepository
from app.infrastructure.vehicle_gateway.fake_vehicle_gateway import FakeVehicleCommandGateway
from app.infrastructure.time.system_clock import SystemClock
from app.infrastructure.ids.uuid_generator import UuidGenerator
from app.application.services.command_policy import CommandPolicy
from app.application.services.telemetry_validation import TelemetryValidation
from app.application.services.alert_rules import AlertRules
from app.application.services.maintenance_rules import MaintenanceRules
from app.application.use_cases.commands.lock_vehicle import LockVehicleUseCase
from app.application.use_cases.commands.unlock_vehicle import UnlockVehicleUseCase
from app.application.use_cases.commands.start_climate import StartClimateUseCase
from app.application.use_cases.commands.stop_climate import StopClimateUseCase
from app.application.use_cases.commands.set_cabin_temperature import SetCabinTemperatureUseCase
from app.application.use_cases.commands.flash_lights import FlashLightsUseCase
from app.application.use_cases.commands.honk_horn import HonkHornUseCase
from app.application.use_cases.commands.open_trunk import OpenTrunkUseCase
from app.application.use_cases.commands.close_windows import CloseWindowsUseCase
from app.application.use_cases.telemetry.ingest_telemetry import IngestTelemetryUseCase
from app.application.use_cases.telemetry.get_vehicle_status import GetVehicleStatusUseCase
from app.application.use_cases.telemetry.get_telemetry_history import GetTelemetryHistoryUseCase
from app.application.use_cases.eligibility.get_command_eligibility import GetCommandEligibilityUseCase
from app.application.use_cases.alerts.evaluate_vehicle_alerts import EvaluateVehicleAlertsUseCase
from app.application.use_cases.alerts.get_active_alerts import GetActiveAlertsUseCase
from app.application.use_cases.alerts.clear_vehicle_alert import ClearVehicleAlertUseCase
from app.application.use_cases.trips.start_trip import StartTripUseCase
from app.application.use_cases.trips.end_trip import EndTripUseCase
from app.application.use_cases.trips.get_current_trip import GetCurrentTripUseCase
from app.application.use_cases.trips.get_trip_summary import GetTripSummaryUseCase
from app.application.use_cases.maintenance.get_maintenance_status import GetMaintenanceStatusUseCase
from app.application.use_cases.maintenance.record_service_reset import RecordServiceResetUseCase
from app.application.use_cases.diagnostics.ingest_diagnostic_codes import IngestDiagnosticCodesUseCase
from app.application.use_cases.diagnostics.get_active_diagnostic_codes import GetActiveDiagnosticCodesUseCase
from app.application.use_cases.diagnostics.clear_diagnostic_code import ClearDiagnosticCodeUseCase


class Container:
    def __init__(self):
        # Infrastructure
        self.command_repo = InMemoryCommandRepository()
        self.telemetry_repo = InMemoryTelemetryRepository()
        self.alert_repo = InMemoryAlertRepository()
        self.trip_repo = InMemoryTripRepository()
        self.maintenance_repo = InMemoryMaintenanceRepository()
        self.diagnostic_repo = InMemoryDiagnosticRepository()
        self.gateway = FakeVehicleCommandGateway()
        self.clock = SystemClock()
        self.id_gen = UuidGenerator()

        # Services
        self.command_policy = CommandPolicy()
        self.telemetry_validation = TelemetryValidation()
        self.alert_rules = AlertRules()
        self.maintenance_rules = MaintenanceRules()

        # Use cases
        self.lock_vehicle = LockVehicleUseCase(
            command_repo=self.command_repo, telemetry_repo=self.telemetry_repo,
            gateway=self.gateway, clock=self.clock, id_gen=self.id_gen, policy=self.command_policy)
        self.unlock_vehicle = UnlockVehicleUseCase(
            command_repo=self.command_repo,
            gateway=self.gateway, clock=self.clock, id_gen=self.id_gen)
        self.start_climate = StartClimateUseCase(
            command_repo=self.command_repo, telemetry_repo=self.telemetry_repo,
            gateway=self.gateway, clock=self.clock, id_gen=self.id_gen, policy=self.command_policy)
        self.stop_climate = StopClimateUseCase(
            command_repo=self.command_repo,
            gateway=self.gateway, clock=self.clock, id_gen=self.id_gen)
        self.set_cabin_temperature = SetCabinTemperatureUseCase(
            command_repo=self.command_repo,
            gateway=self.gateway, clock=self.clock, id_gen=self.id_gen, policy=self.command_policy)
        self.flash_lights = FlashLightsUseCase(
            command_repo=self.command_repo,
            gateway=self.gateway, clock=self.clock, id_gen=self.id_gen)
        self.honk_horn = HonkHornUseCase(
            command_repo=self.command_repo,
            gateway=self.gateway, clock=self.clock, id_gen=self.id_gen, policy=self.command_policy)
        self.open_trunk = OpenTrunkUseCase(
            command_repo=self.command_repo, telemetry_repo=self.telemetry_repo,
            gateway=self.gateway, clock=self.clock, id_gen=self.id_gen, policy=self.command_policy)
        self.close_windows = CloseWindowsUseCase(
            command_repo=self.command_repo,
            gateway=self.gateway, clock=self.clock, id_gen=self.id_gen)
        self.ingest_telemetry = IngestTelemetryUseCase(
            telemetry_repo=self.telemetry_repo, clock=self.clock, validation=self.telemetry_validation)
        self.get_vehicle_status = GetVehicleStatusUseCase(telemetry_repo=self.telemetry_repo)
        self.get_telemetry_history = GetTelemetryHistoryUseCase(telemetry_repo=self.telemetry_repo)
        self.get_command_eligibility = GetCommandEligibilityUseCase(telemetry_repo=self.telemetry_repo)
        self.evaluate_vehicle_alerts = EvaluateVehicleAlertsUseCase(
            telemetry_repo=self.telemetry_repo, alert_repo=self.alert_repo,
            clock=self.clock, rules=self.alert_rules)
        self.get_active_alerts = GetActiveAlertsUseCase(alert_repo=self.alert_repo)
        self.clear_vehicle_alert = ClearVehicleAlertUseCase(alert_repo=self.alert_repo)
        self.start_trip = StartTripUseCase(
            trip_repo=self.trip_repo, telemetry_repo=self.telemetry_repo,
            clock=self.clock, id_gen=self.id_gen)
        self.end_trip = EndTripUseCase(
            trip_repo=self.trip_repo, telemetry_repo=self.telemetry_repo, clock=self.clock)
        self.get_current_trip = GetCurrentTripUseCase(trip_repo=self.trip_repo)
        self.get_trip_summary = GetTripSummaryUseCase(trip_repo=self.trip_repo)
        self.get_maintenance_status = GetMaintenanceStatusUseCase(
            maintenance_repo=self.maintenance_repo, telemetry_repo=self.telemetry_repo,
            rules=self.maintenance_rules)
        self.record_service_reset = RecordServiceResetUseCase(
            maintenance_repo=self.maintenance_repo, telemetry_repo=self.telemetry_repo, clock=self.clock)
        self.ingest_diagnostic_codes = IngestDiagnosticCodesUseCase(
            diagnostic_repo=self.diagnostic_repo, clock=self.clock)
        self.get_active_diagnostic_codes = GetActiveDiagnosticCodesUseCase(diagnostic_repo=self.diagnostic_repo)
        self.clear_diagnostic_code = ClearDiagnosticCodeUseCase(diagnostic_repo=self.diagnostic_repo)
