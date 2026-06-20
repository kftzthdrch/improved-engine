# Chapter 20: Hexagonal Architecture vs Clean Architecture

## Learning Objective

Understand the origin, structure, and vocabulary of both hexagonal architecture and clean
architecture, identify where they overlap and where they differ, and decide with confidence
which pattern fits a given project.

---

## Relevant Files in This Project

```
app/domain/           ← domain layer (maps to "Entities" in Clean, "center" in Hexagonal)
app/application/      ← use cases + ports (maps to "Use Cases" in Clean, "inner hexagon" in Hexagonal)
app/infrastructure/   ← adapters (maps to "Frameworks & Drivers" in Clean, "outer adapters" in Hexagonal)
app/api/              ← controllers/presenters (maps to "Interface Adapters" in Clean, "inbound adapters" in Hexagonal)
```

---

## 1. Where Both Come From

### Hexagonal Architecture (Ports & Adapters)

Coined by **Alistair Cockburn** around 2005.

The central metaphor is a hexagon — not because six sides are special, but because a hexagon
visually gives enough room to draw multiple ports on each side without implying a strict hierarchy.
The key claim: *an application should be equally drivable by any outside actor* — a browser,
a test, a CLI, a message queue — and should work in complete isolation from its database.

```
         [Browser]   [Test Suite]   [CLI]
              \            |           /
               ▼           ▼          ▼
          ┌────────────────────────────┐
          │  inbound adapters (HTTP,   │
          │  TestClient, argparse...)  │
          │  ┌──────────────────────┐  │
          │  │   Application Core   │  │   ← The Hexagon
          │  │   (use cases +       │  │
          │  │    domain model)     │  │
          │  └──────────────────────┘  │
          │  outbound adapters (repos, │
          │  gateways, clocks, ...)    │
          └────────────────────────────┘
               ▲           ▲          ▲
              /            |           \
       [In-Memory DB]  [Fake Gateway]  [Real DB]
```

Cockburn's two key rules:
1. The application is at the center. It does not know about adapters.
2. Adapters talk to the application only through **ports** (interfaces).

### Clean Architecture

Described by **Robert C. Martin ("Uncle Bob")** in 2012, popularised in his 2017 book
*Clean Architecture: A Craftsman's Guide to Software Structure and Design*.

Clean Architecture draws **four explicit concentric rings** and gives each ring a name:

```
  ┌─────────────────────────────────────────┐
  │  Frameworks & Drivers                   │  ← outermost ring
  │  ┌───────────────────────────────────┐  │
  │  │  Interface Adapters               │  │
  │  │  ┌─────────────────────────────┐  │  │
  │  │  │  Use Cases                  │  │  │
  │  │  │  ┌───────────────────────┐  │  │  │
  │  │  │  │  Entities             │  │  │  │
  │  │  │  │  (Enterprise rules)   │  │  │  │
  │  │  │  └───────────────────────┘  │  │  │
  │  │  └─────────────────────────────┘  │  │
  │  └───────────────────────────────────┘  │
  └─────────────────────────────────────────┘
```

Martin's **Dependency Rule**: source code dependencies must point inward only. Nothing in an
inner ring can know about anything in an outer ring.

---

## 2. Vocabulary Comparison

| Concept | Hexagonal Architecture | Clean Architecture |
|---|---|---|
| Business concepts | Domain model / Application Core | Entities |
| Orchestration logic | Use Cases (implied, not formally named) | Use Cases (explicitly a ring) |
| Framework glue | Adapters | Interface Adapters + Frameworks & Drivers |
| Interfaces between layers | Ports (Protocol / interface) | Boundaries / Interfaces |
| Inbound callers | Driving adapters | Controllers / Presenters |
| Outbound systems | Driven adapters | Gateways / Repositories |
| Dependency direction rule | Adapters depend on ports; ports belong to the core | Dependency Rule: always inward |

The concepts map almost 1-to-1. The difference is **how explicitly each ring is named and
separated**.

---

## 3. Where They Agree

Both architectures share the same foundational idea:

1. **Business logic must not depend on frameworks.** FastAPI, Django, SQLAlchemy — these are
   tools. The core application should be testable without them.

2. **Dependency inversion.** The inner layers define interfaces. Outer layers implement them.
   The database depends on the application, not the other way around.

3. **Testability as a design goal.** If you can instantiate your use cases with no web
   server and no database, your architecture is correct.

4. **Replaceability.** Switching from in-memory repositories to a PostgreSQL adapter should
   require zero changes to the domain or use case layer.

This project demonstrates all four properties:

```python
# No FastAPI. No database. Fully testable.
use_case = LockVehicleUseCase(
    command_repo=InMemoryCommandRepository(),
    telemetry_repo=InMemoryTelemetryRepository(),
    gateway=FakeVehicleCommandGateway(),
    clock=SystemClock(),
    id_gen=UuidGenerator(),
    policy=CommandPolicy(),
)
result = use_case.execute(VehicleId("VH-001"))
```

---

## 4. Where They Differ

### 4.1 Granularity of the Domain Layer

**Hexagonal** does not prescribe how to structure the inside of the hexagon. It says: "protect
the core from adapters." What lives inside the core is up to you.

**Clean Architecture** explicitly splits the inside into two rings:

- **Entities** — enterprise-wide business rules. Objects that would exist even if you had
  no application software. In this project: `Command`, `TelemetrySnapshot`, `VehicleId`.

- **Use Cases** — application-specific business rules. The orchestration of entities to
  accomplish one task. In this project: `LockVehicleUseCase`, `IngestTelemetryUseCase`.

This distinction matters in large systems. An "Entity" might be shared across many bounded
contexts. A "Use Case" is specific to one workflow.

In a small project — like this one — both layers often merge into one `application/` package.
Hexagonal handles that gracefully. Clean Architecture asks you to be disciplined about it.

### 4.2 Presenter Pattern

Clean Architecture formally defines a **Presenter** — an object that transforms use case
output into a view model before it reaches the UI layer. The data flow is:

```
Controller → Use Case → Output Port → Presenter → View Model → UI
```

Hexagonal does not mandate a presenter. It says: adapters on both sides.

FastAPI projects (including this one) typically skip the presenter and let the route handler
do the mapping inline:

```python
# app/api/routes/commands.py — mapping done inline, no separate Presenter
def _to_response(cmd) -> CommandResponse:
    return CommandResponse(id=cmd.id.value, status=cmd.status.value, ...)
```

In larger systems or when multiple UIs consume the same use case, a dedicated presenter
class becomes valuable. Clean Architecture names and encourages it. Hexagonal leaves it
as a design choice.

### 4.3 Interface Adapters Ring

Clean Architecture defines a dedicated "Interface Adapters" ring that sits between the
application core and the outer framework ring. This ring contains:

- **Controllers** (parse input, call use cases)
- **Presenters** (format output)
- **Gateways** (define abstract I/O interfaces for the Use Case ring to depend on)

Hexagonal collapses this into "adapters" without mandating the separation between
controller and presenter.

In practice, `app/api/` in this project is the Interface Adapters ring even though it is
called "api" — it contains controllers (route handlers), presenters (the `_to_response`
functions), and gateway definitions live in `app/application/ports/`.

### 4.4 The "Frameworks & Drivers" Ring

Clean Architecture names the outermost ring "Frameworks & Drivers" and treats FastAPI,
the database ORM, and the web server as belonging here. The rule: nothing in this ring
should be imported by any inner ring.

Hexagonal uses the word "adapter" for this layer and says the same thing: adapters depend
on ports, never the reverse.

---

## 5. Summary Table

| Property | Hexagonal | Clean Architecture |
|---|---|---|
| Year introduced | ~2005 (Cockburn) | 2012 / 2017 (Martin) |
| Number of explicit layers | 2 (inside / outside) | 4 (Entities, Use Cases, Interface Adapters, Frameworks) |
| Domain layer split (Entities vs Use Cases) | Not mandated | Explicitly required |
| Presenter pattern | Not defined | Formally defined |
| Ports and Adapters vocabulary | Central concept | Present but not the primary vocabulary |
| Primary teaching metaphor | Hexagon with ports | Concentric rings with arrows |
| Dependency direction rule | Adapters depend on ports | Dependency Rule: always inward |
| Framework coupling | Zero (by design) | Zero (by design) |
| Suitability for small projects | Excellent | Good, but more ceremony |
| Suitability for large enterprises | Good | Excellent — more structure enforced |

---

## 6. When to Choose Hexagonal

Choose hexagonal architecture when:

- **You want the simplest mental model.** Two concepts — ports and adapters — are enough to
  explain the architecture to a new team member.

- **Your team is new to architecture patterns.** Start with "nothing inside the hexagon may
  import anything outside the hexagon." That one rule gets you 80% of the value.

- **Your domain layer is small and doesn't need subdivision.** A service with fewer than
  ~15 use cases doesn't need to split Entities from Use Cases formally.

- **You are building a microservice or bounded context.** Hexagonal maps naturally to
  microservices: each service has one hexagon.

- **You want explicit adapter swappability.** The ports concept makes the "replace the
  database without touching business logic" story very concrete and teachable — as this
  project demonstrates.

This project chose hexagonal for all of these reasons.

---

## 7. When to Choose Clean Architecture

Choose clean architecture when:

- **You have a large domain shared across multiple applications.** The explicit Entities
  ring gives you a place to put enterprise-wide rules that no single use case owns.

- **You want a formal presenter pattern.** If your application has multiple front-ends
  (REST API, gRPC, CLI) that need different views of the same use case output, a
  dedicated presenter class — as Clean Architecture describes — keeps routes thin.

- **Your team benefits from more structure.** Clean Architecture's four named rings provide
  a stricter scaffold that reduces architectural debate in large teams.

- **You want to follow an established, widely documented pattern.** The Clean Architecture
  book and community resources are extensive. Onboarding developers who have read the book
  is straightforward.

---

## 8. Practical Truth: They Are Compatible

In production codebases, most teams use both vocabularies interchangeably. A common outcome:

```
app/domain/           → Entities ring (Clean) = inside the hexagon (Hexagonal)
app/application/      → Use Cases ring (Clean) = inside the hexagon (Hexagonal)
  ports/              → Boundaries / Output Ports (Clean) = Ports (Hexagonal)
  use_cases/          → Use Cases (both)
  services/           → Domain Services (both)
app/infrastructure/   → Frameworks & Drivers (Clean) = Driven Adapters (Hexagonal)
app/api/              → Interface Adapters (Clean) = Driving Adapters (Hexagonal)
```

This project's structure satisfies both patterns. You could describe it as hexagonal or
as clean architecture and be correct both times.

The meaningful choice is not "hexagonal vs clean" — it is "do we enforce architectural
boundaries at all?" Both patterns enforce the same boundary: business logic has no
knowledge of databases, frameworks, or HTTP.

---

## 9. Anti-Patterns to Avoid

**Putting business rules in the wrong ring:**

```python
# Bad — business rule in a route handler (violates both patterns)
@router.post("/vehicles/{vehicle_id}/commands/lock")
def lock(vehicle_id: str):
    telemetry = db.query(Telemetry).filter_by(vehicle_id=vehicle_id).first()
    if telemetry.speed_kph > 0:
        raise HTTPException(409, "Vehicle is moving")  # ← business rule here
    ...
```

```python
# Good — route delegates to use case, use case enforces the rule
@router.post("/vehicles/{vehicle_id}/commands/lock")
def lock(vehicle_id: str, use_case=Depends(get_lock_vehicle_use_case)):
    cmd = use_case.execute(VehicleId(vehicle_id))  # ← rule lives in CommandPolicy
    return _to_response(cmd)
```

**Importing infrastructure from domain or use cases:**

```python
# Bad — use case knows about the concrete repository (violates both patterns)
from app.infrastructure.persistence.in_memory_command_repository import InMemoryCommandRepository

class LockVehicleUseCase:
    def __init__(self):
        self.repo = InMemoryCommandRepository()  # ← wrong layer
```

```python
# Good — use case depends on the port (Protocol), not the adapter
from app.application.ports.command_repository import CommandRepository

@dataclass
class LockVehicleUseCase:
    command_repo: CommandRepository  # ← correct: port, not adapter
```

---

## 10. Exercises

1. **Identify the rings in this project.** Open `app/composition/container.py` and map
   each import to its Clean Architecture ring (Entities, Use Cases, Interface Adapters,
   Frameworks & Drivers). Which ring does `Container` itself belong to?

2. **Add a Presenter.** Create `app/api/presenters/command_presenter.py` with a
   `CommandPresenter` class that has a static `to_response(cmd: Command) -> CommandResponse`
   method. Replace the `_to_response` function in `app/api/routes/commands.py` with a call
   to this presenter. Does this change improve or complicate the code? Why?

3. **Separate Entities from Use Cases.** Split `app/domain/` into `app/domain/entities/`
   (containing domain models) and `app/domain/value_objects/` (unchanged). Update all
   imports. This moves the project closer to Clean Architecture's explicit entity ring. Is
   the result clearer or more complex for this project's size?

---

## Review Checklist

- [ ] Can you name the author and year of both patterns?
- [ ] Can you draw both architectural diagrams from memory?
- [ ] Can you map the folders in this project to the vocabulary of both patterns?
- [ ] Can you explain the one shared rule that both patterns enforce?
- [ ] Can you explain the main difference (granularity of inner rings, presenter pattern)?
- [ ] Can you articulate one scenario where you would choose hexagonal over clean, and one
      scenario where you would choose clean over hexagonal?
- [ ] Can you identify an anti-pattern that violates both architectures in a code review?
