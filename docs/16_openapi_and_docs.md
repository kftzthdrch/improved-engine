# Chapter 16: OpenAPI and Docs

## Learning Objective

Understand what FastAPI generates automatically from the project's code — OpenAPI schemas, interactive documentation at `/docs`, and the role of tags, `response_model`, and Pydantic schemas in shaping what appears in the documentation.

---

## What FastAPI Generates Automatically

When you start the application, FastAPI inspects every registered route and Pydantic schema and generates an OpenAPI 3 specification. No manual specification writing is required.

The specification is served at three URLs:

- `/openapi.json` — the raw OpenAPI 3 JSON document.
- `/docs` — Swagger UI: an interactive browser interface. You can expand endpoints, fill in fields, and click "Execute" to make a real HTTP request.
- `/redoc` — ReDoc: a read-only, well-formatted reference view. Better for reading documentation; worse for testing.

---

## The App Metadata

From `create_app()` in `app/main.py`:

```python
app = FastAPI(
    title="Automotive Vehicle Command & Telematics Service",
    description="A hexagonal architecture learning project using FastAPI",
    version="0.1.0",
    lifespan=lifespan,
)
```

These three fields appear at the top of both `/docs` and `/redoc`. The `title` becomes the heading. The `description` appears below it. The `version` appears in the top-right corner.

---

## Tags

Tags group endpoints into sections in the documentation UI. Each router declares its tag:

```python
# app/api/routes/commands.py
router = APIRouter(tags=["commands"])

# app/api/routes/telemetry.py
router = APIRouter(tags=["telemetry"])

# app/api/routes/alerts.py
router = APIRouter(tags=["alerts"])
```

In `/docs`, all endpoints from `commands.py` appear under the "commands" section, all from `telemetry.py` under "telemetry", and so on. Tags make a large API navigable.

The tag values in this project match the domain area names: `commands`, `telemetry`, `alerts`, `trips`, `maintenance`, `diagnostics`, `eligibility`, `health`, `ui`.

---

## Response Models as OpenAPI Schemas

The `response_model` parameter on each route decorator causes FastAPI to:

1. Include the Pydantic schema in the OpenAPI spec as a named schema (under `components/schemas/`).
2. Reference that schema in the route's `responses.200.content.application/json.schema`.
3. Display the schema fields in the response section of the endpoint in `/docs` and `/redoc`.

Example:

```python
@router.post("/vehicles/{vehicle_id}/commands/lock", response_model=CommandResponse, status_code=200)
def lock_vehicle(...):
```

In `/docs`, the lock endpoint's response section shows all fields of `CommandResponse`:

- `id` (string)
- `vehicle_id` (string)
- `command_type` (string)
- `status` (string)
- `created_at` (string, date-time format)
- `updated_at` (string, date-time format)
- `payload` (object)
- `failure_reason` (string, nullable)

FastAPI derives all of this automatically from the `CommandResponse` class definition.

---

## Request Body Schemas

When a route has a Pydantic request body parameter, FastAPI includes the schema in the OpenAPI spec and renders it in `/docs` as the "Request body" section with a JSON example.

For `TelemetryIngestRequest`:

```json
{
  "speed_kph": 0,
  "battery_percent": 0,
  "odometer_km": 0,
  "door_locked": true,
  "cabin_temperature_c": 0
}
```

FastAPI generates this example automatically from the field types. Pydantic's `Field(example=...)` can be used to provide more realistic example values.

---

## Path Parameters in Docs

Path parameters declared with `Path(...)` appear in the "Parameters" section of each endpoint in `/docs`:

```python
def lock_vehicle(vehicle_id: str = Path(...), ...):
```

The documentation shows `vehicle_id` as a required path parameter of type `string`.

---

## Error Response Documentation

The `ErrorResponse` schema in `app/api/schemas/error_schemas.py` documents the consistent error shape:

```python
class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail
```

These schemas are not used as `response_model` on any route (because exception handlers return `JSONResponse` directly, bypassing FastAPI's response model system). However, they document the shape for human readers and could be added as explicit error responses in the OpenAPI spec with additional configuration.

---

## Using /docs During Development

Workflow for testing a new endpoint during development:

1. Start the app: `uvicorn "app.main:create_app" --reload --factory`
2. Open `http://localhost:8000/docs` in a browser.
3. Find your endpoint under the correct tag section.
4. Click the endpoint to expand it.
5. Click "Try it out".
6. Fill in the required parameters and request body.
7. Click "Execute".
8. Read the response — status code, headers, and JSON body.

This is faster than writing a curl command or using Postman for exploratory testing. All the schema information is already there — you do not need to remember field names.

---

## What /openapi.json Contains

A truncated example of the lock endpoint in the generated JSON:

```json
{
  "/vehicles/{vehicle_id}/commands/lock": {
    "post": {
      "tags": ["commands"],
      "summary": "Lock Vehicle",
      "operationId": "lock_vehicle_vehicles__vehicle_id__commands_lock_post",
      "parameters": [
        {
          "name": "vehicle_id",
          "in": "path",
          "required": true,
          "schema": {"type": "string"}
        }
      ],
      "responses": {
        "200": {
          "description": "Successful Response",
          "content": {
            "application/json": {
              "schema": {"$ref": "#/components/schemas/CommandResponse"}
            }
          }
        }
      }
    }
  }
}
```

The `operationId` is auto-generated from the function name and route path. It can be customized with `operation_id=` on the decorator.

---

## Enriching the Documentation

FastAPI supports several ways to add more detail to the generated docs:

**Docstrings on route functions** appear as the endpoint description:

```python
@router.post("/vehicles/{vehicle_id}/commands/lock", ...)
def lock_vehicle(...):
    """
    Issue a lock command to the specified vehicle.

    The command will be rejected if the vehicle is currently moving.
    Returns the command record with its final status.
    """
```

**`Field()` with description and example** on Pydantic models:

```python
from pydantic import BaseModel, Field

class TelemetryIngestRequest(BaseModel):
    speed_kph: float = Field(..., description="Current speed in km/h", example=60.0)
    battery_percent: float = Field(..., description="Battery level 0–100", example=85.0)
```

**`responses=` on the decorator** to document error responses explicitly:

```python
@router.post(
    "/vehicles/{vehicle_id}/commands/lock",
    response_model=CommandResponse,
    responses={409: {"model": ErrorResponse, "description": "Command rejected"}},
)
```

---

## Anti-Patterns to Avoid

**Relying on `/docs` as the only API documentation.** `/docs` is excellent for development exploration but is not a substitute for written documentation explaining business rules, workflows, and error meanings.

**Not adding docstrings to route functions.** The auto-generated `summary` is just the function name converted to title case ("Lock Vehicle"). A docstring with the business context is far more useful.

**Not specifying `response_model`.** Without it, FastAPI cannot generate the response schema. The response section in `/docs` will be empty or incorrect, and the output will not be validated.

---

## Exercises

1. Start the app and open `/docs`. Find the telemetry ingest endpoint. Click "Try it out." Send a telemetry record for `VH-DEMO`. Then find the vehicle status endpoint and retrieve the status. Confirm the values match what you sent.

2. Add a docstring to `lock_vehicle` in `app/api/routes/commands.py` explaining when the command is rejected. Start the app and confirm the description appears in `/docs`.

3. Open `/openapi.json` in your browser. Find the `CommandResponse` schema under `components.schemas`. Count the number of fields. Confirm it matches the `CommandResponse` Pydantic class.

---

## Review Checklist

- [ ] I know the three URLs where FastAPI serves OpenAPI documentation.
- [ ] I understand how `tags` control grouping in `/docs`.
- [ ] I know what `response_model` contributes to the OpenAPI spec.
- [ ] I can use `/docs` to test an endpoint interactively.
- [ ] I know how to add a docstring to improve the generated documentation.
