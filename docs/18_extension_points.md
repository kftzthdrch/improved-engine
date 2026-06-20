# Chapter 18: Extension Points

## Learning Objective

Understand how to add seven major capabilities to this project in the future — database, MQTT gateway, ROS adapter, authentication, background tasks, WebSockets, and Docker — without breaking any existing code.

---

## The Extension Principle

Every extension described in this chapter follows the same pattern:

> **Add a new adapter. Change only `app/composition/container.py` to wire it in. Touch nothing in `app/domain/` or `app/application/`.**

The domain and application layers are stable. Adapters are replaceable. This is the payoff of hexagonal architecture.

---

## Extension 1: Database Adapter

**Files that change:** new files in `app/infrastructure/persistence/`, edits to `container.py` and `pyproject.toml`.

**Files that do not change:** `app/domain/`, `app/application/`, `app/api/`, `app/ui/`, all unit tests, all integration test logic.

Create one new repository class per domain area, each implementing the matching port Protocol. For example, a SQLAlchemy telemetry repository:

```python
# app/infrastructure/persistence/sqlalchemy_telemetry_repository.py
from sqlalchemy.orm import Session
from app.domain.models.telemetry import TelemetrySnapshot
from app.domain.value_objects.vehicle_id import VehicleId

class SQLAlchemyTelemetryRepository:
    def __init__(self, session: Session):
        self._session = session

    def save(self, snapshot: TelemetrySnapshot) -> None:
        # convert snapshot to ORM model and commit
        ...

    def get_latest(self, vehicle_id: VehicleId) -> TelemetrySnapshot | None:
        # query and convert ORM row to domain snapshot
        ...

    def get_history(self, vehicle_id: VehicleId) -> list[TelemetrySnapshot]:
        ...
```

This class satisfies `TelemetryRepository` Protocol structurally. Wire it in by editing two lines in `container.py`:

```python
# Before
self.telemetry_repo = InMemoryTelemetryRepository()

# After
self.telemetry_repo = SQLAlchemyTelemetryRepository(session=get_session())
```

`IngestTelemetryUseCase` never changes. It calls `self.telemetry_repo.save(...)` regardless of whether the repo is in-memory or SQLAlchemy.

Update the no-database architecture test if you want to permit database imports in `app/infrastructure/` while still forbidding them in `app/domain/` and `app/application/`.

---

## Extension 2: MQTT Vehicle Command Gateway

**Files that change:** new `app/infrastructure/vehicle_gateway/mqtt_vehicle_gateway.py`, edits to `container.py` and `pyproject.toml`.

**Files that do not change:** all command use cases (they call `self.gateway.send(...)` unchanged).

```python
# app/infrastructure/vehicle_gateway/mqtt_vehicle_gateway.py
import json
import paho.mqtt.client as mqtt
from app.application.ports.vehicle_command_gateway import GatewayResult
from app.domain.enums import CommandType
from app.domain.value_objects.vehicle_id import VehicleId
from app.domain.value_objects.command_id import CommandId

class MQTTVehicleCommandGateway:
    def __init__(self, broker_host: str, broker_port: int = 1883):
        self._client = mqtt.Client()
        self._client.connect(broker_host, broker_port)

    def send(
        self,
        vehicle_id: VehicleId,
        command_id: CommandId,
        command_type: CommandType,
        payload: dict,
    ) -> GatewayResult:
        topic = f"vehicles/{vehicle_id.value}/commands"
        message = json.dumps({"command_id": command_id.value, "type": command_type.value, **payload})
        result = self._client.publish(topic, message)
        return GatewayResult(success=(result.rc == mqtt.MQTT_ERR_SUCCESS))
```

Swap in `container.py`:

```python
self.gateway = MQTTVehicleCommandGateway(broker_host="localhost")
```

---

## Extension 3: ROS Adapter

**Context:** ROS 2 (Robot Operating System) uses topics and services to communicate between nodes. A vehicle running ROS 2 would expose command services and publish telemetry topics.

**Files that change:** new `app/infrastructure/vehicle_gateway/ros_vehicle_gateway.py` (outbound adapter) and new `app/infrastructure/telemetry_listener/ros_telemetry_listener.py` (inbound adapter).

**Files that do not change:** `IngestTelemetryUseCase`, `LockVehicleUseCase`, and all other use cases. They receive a `VehicleId` and primitive values; the source is irrelevant.

The ROS telemetry listener is an *inbound adapter* — it drives the application by calling a use case, just as an HTTP route does:

```python
# app/infrastructure/telemetry_listener/ros_telemetry_listener.py
import rclpy
from rclpy.node import Node

class ROSTelemetryListener(Node):
    def __init__(self, ingest_use_case):
        super().__init__("telemetry_listener")
        self._use_case = ingest_use_case
        self.create_subscription(
            NavSatFix, "/vehicle/telemetry", self._on_telemetry, 10
        )

    def _on_telemetry(self, msg):
        from app.domain.value_objects.vehicle_id import VehicleId
        self._use_case.execute(
            VehicleId(msg.header.frame_id),
            speed_kph=0.0,
            battery_percent=100.0,
            odometer_km=0.0,
            door_locked=True,
            cabin_temperature_c=22.0,
        )
```

See the `user-skills:ros2` skill for project-specific ROS 2 guidelines.

---

## Extension 4: Authentication

**Files that change:** new `app/api/middleware/auth.py`, one edit to `create_app()` in `app/main.py`.

**Files that do not change:** every file in `app/domain/`, `app/application/`, and `app/infrastructure/`. Use cases do not receive user context unless you explicitly add it to `execute()` signatures.

FastAPI middleware intercepts every request before it reaches a route handler:

```python
# app/api/middleware/auth.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_key: str):
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(self, request: Request, call_next):
        token = request.headers.get("X-API-Key")
        if token != self._api_key:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return await call_next(request)
```

Register in `create_app()`:

```python
app.add_middleware(APIKeyMiddleware, api_key="secret-key")
```

Authentication sits entirely outside the hexagon. Use cases never know a request was authenticated.

---

## Extension 5: Background Tasks

**Files that change:** one route handler in `app/api/routes/`.

**Files that do not change:** all use cases.

FastAPI's `BackgroundTasks` runs work after the response has been sent. Example: evaluate alerts automatically after telemetry ingest, without making the client wait:

```python
# app/api/routes/telemetry.py
from fastapi import BackgroundTasks

@router.post("/vehicles/{vehicle_id}/telemetry", response_model=TelemetryResponse, status_code=201)
def ingest_telemetry(
    body: TelemetryIngestRequest,
    background_tasks: BackgroundTasks,
    vehicle_id: str = Path(...),
    ingest_use_case=Depends(get_ingest_telemetry_use_case),
    alert_use_case=Depends(get_evaluate_alerts_use_case),
):
    snap = ingest_use_case.execute(VehicleId(vehicle_id), ...)
    background_tasks.add_task(alert_use_case.execute, VehicleId(vehicle_id))
    return _to_telemetry_response(snap)
```

The client receives the telemetry response immediately. `EvaluateVehicleAlertsUseCase.execute()` runs in the background after the response is sent — it is called the same way as always, with a `VehicleId`.

---

## Extension 6: WebSockets

**Files that change:** new `app/api/routes/ws.py`, one `include_router` call in `create_app()`.

**Files that do not change:** all use cases, all domain models, all infrastructure adapters.

WebSockets let the server push alerts to the browser without polling. A connection manager tracks active WebSocket connections per vehicle:

```python
# app/api/routes/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])
_connections: dict[str, list[WebSocket]] = {}

@router.websocket("/ws/vehicles/{vehicle_id}/alerts")
async def alert_stream(websocket: WebSocket, vehicle_id: str):
    await websocket.accept()
    _connections.setdefault(vehicle_id, []).append(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive ping
    except WebSocketDisconnect:
        _connections[vehicle_id].remove(websocket)

async def broadcast_alerts(vehicle_id: str, alerts: list) -> None:
    for ws in _connections.get(vehicle_id, []):
        await ws.send_json([a.alert_type.value for a in alerts])
```

The alert evaluation route handler calls `broadcast_alerts(...)` after running the use case. `EvaluateVehicleAlertsUseCase` returns a list of `VehicleAlert` objects — it does not know or care whether they are sent over HTTP, WebSocket, or logged to a file.

---

## Extension 7: Docker

**Files that change:** new `Dockerfile` and optionally `docker-compose.yml` at the project root.

**Files that do not change:** every Python file in the project.

Docker is purely an operational concern. No application code changes.

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install .
COPY app/ ./app/

EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

The `--factory` flag tells uvicorn to call `create_app()` to obtain the application instance, exactly as in local development.

If you added a database (Extension 1), `docker-compose.yml` would add a PostgreSQL service. The application container reads a `DATABASE_URL` environment variable and passes it to the SQLAlchemy repository. Nothing in the application code changes — only `container.py` reads the environment variable.

---

## Extension Summary

| Extension | New files | Edited files | Untouched |
| --------- | --------- | ------------ | --------- |
| Database adapter | `infrastructure/persistence/sqlalchemy_*.py` | `container.py`, `pyproject.toml` | domain, application, api |
| MQTT gateway | `infrastructure/vehicle_gateway/mqtt_*.py` | `container.py`, `pyproject.toml` | domain, application, api |
| ROS adapter | `infrastructure/vehicle_gateway/ros_*.py`, `infrastructure/telemetry_listener/ros_*.py` | `container.py`, `pyproject.toml` | domain, application |
| Authentication | `api/middleware/auth.py` | `main.py` | domain, application, infrastructure |
| Background tasks | — | one route handler | domain, application, infrastructure |
| WebSockets | `api/routes/ws.py` | `main.py` | domain, application, infrastructure |
| Docker | `Dockerfile`, `docker-compose.yml` | nothing | everything |

---

## Review Checklist

- [ ] I can describe the steps to add a SQLAlchemy repository without changing any use case.
- [ ] I understand that authentication middleware sits entirely outside the hexagon.
- [ ] I can explain how a ROS telemetry subscriber is an inbound adapter.
- [ ] I know that WebSockets add a new inbound adapter but leave use cases unchanged.
- [ ] I understand that Docker requires zero application code changes.
