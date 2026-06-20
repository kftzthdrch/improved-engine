# Chapter 12: UI with Templates and Static Files

## Learning Objective

Understand how the browser-based dashboard is wired into the project, why the browser is an inbound adapter, how Jinja2Templates and StaticFiles work in FastAPI, and why vanilla JavaScript was chosen over a frontend framework.

---

## The UI as an Inbound Adapter

The browser is an inbound adapter in exactly the same sense as the FastAPI routes themselves. It sits outside the hexagon and communicates with the application through HTTP calls to the REST API.

The browser:

- Sends HTTP GET/POST/DELETE requests to the same endpoints documented in `/docs`.
- Receives JSON responses.
- Never calls a use case, a repository, or a domain model directly.
- Never has direct access to Python memory.

This is an important architectural point: the UI layer is not a special case. It is just another client. If you replaced the vanilla JS dashboard with a React SPA or a mobile app, nothing in `app/application/` or `app/domain/` would change.

---

## How the Dashboard Is Served

### The Template Route

File: `app/api/routes/ui.py`

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(tags=["ui"])

_templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "ui", "templates")
templates = Jinja2Templates(directory=_templates_dir)

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request, "index.html")
```

When a browser navigates to `http://localhost:8000/`, FastAPI calls `dashboard()`. Jinja2Templates renders `app/ui/templates/index.html` and returns it as an HTML response. The browser displays the rendered HTML.

`response_class=HTMLResponse` tells FastAPI to send a `Content-Type: text/html` header. Without it, FastAPI defaults to `Content-Type: application/json`.

### Static Files Mount

File: `app/main.py`

```python
static_dir = os.path.join(os.path.dirname(__file__), "ui", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
```

`app.mount("/static", ...)` registers a sub-application that serves files from the `app/ui/static/` directory. Any request to `/static/app.js` serves `app/ui/static/app.js` directly, without invoking any route handler. FastAPI handles MIME types, caching headers, and range requests automatically.

The HTML template references the static files:

```html
<link rel="stylesheet" href="/static/styles.css">
<script src="/static/app.js"></script>
```

---

## The Jinja2 Template

File: `app/ui/templates/index.html`

The template is a standard HTML5 document. Because this project uses server-side rendering only for the initial page load (no template variables are passed from Python to the template), the Jinja2 template is essentially just HTML. It could work as a static file.

The reason for using `Jinja2Templates` anyway:

- It follows the FastAPI convention for server-side rendering.
- It allows adding template variables later without restructuring (e.g., passing the app version or a CSRF token).
- `TemplateResponse` handles the `Content-Type` and response encoding correctly.

---

## The JavaScript Layer

File: `app/ui/static/app.js`

The JavaScript file uses the browser's native `fetch()` API to call the REST endpoints. There is no bundler, no transpiler, no npm, and no frontend framework. A sample interaction:

```javascript
// Pseudocode of the pattern used in app.js
async function lockVehicle(vehicleId) {
    const response = await fetch(`/vehicles/${vehicleId}/commands/lock`, {
        method: "POST",
    });
    const data = await response.json();
    if (response.ok) {
        displayCommandResult(data);
    } else {
        displayError(data.error.code, data.error.message);
    }
}
```

The error handler reads `data.error.code` and `data.error.message` — the consistent error shape defined in `app/api/exception_handlers.py`. This is the payoff of having a uniform error response structure: the UI only needs one error-display path.

---

## Why No React, Vue, or Angular?

This is a backend architecture learning project. A frontend framework would:

- Add a multi-megabyte `node_modules` directory.
- Require a separate build step (webpack, vite, etc.).
- Introduce a second architecture concern (component hierarchy, state management).
- Make it harder to focus on the Python architecture patterns being taught.

Vanilla JavaScript with `fetch()` is sufficient to demonstrate that the browser communicates with the application only through HTTP. The architecture lesson is about the backend — the frontend is just a client.

---

## Why the UI Does Not Know About Use Cases

A common mistake in beginners' projects is to put business logic in the UI JavaScript: "if battery is below 20%, disable the climate button." This duplicates the rule that `CommandPolicy.enforce_battery_sufficient()` already enforces.

In this project the UI does not duplicate any policy. It sends requests and displays results. If the backend rejects a climate command because battery is low (409 with `COMMAND_REJECTED`), the UI displays the error message. The rule lives once, in Python, in `app/application/services/command_policy.py`.

---

## File Organization

```text
app/ui/
├── templates/
│   └── index.html          # Jinja2 template (initial HTML load)
└── static/
    ├── app.js              # Vanilla JS, fetch() calls
    └── styles.css          # Dashboard styles
```

The UI files are inside `app/ui/` rather than at the project root because they are part of the application package. They are served at runtime by FastAPI, not by a separate static file server.

---

## Adding a New UI Section

If you wanted to add a "Diagnostics" section to the dashboard, the steps are:

1. Add HTML markup to `app/ui/templates/index.html` (a section with a vehicle ID input and a button).
2. Add a `fetchDiagnostics(vehicleId)` function to `app/ui/static/app.js` that calls `GET /vehicles/{vehicleId}/diagnostics`.
3. Display the returned list of `DiagnosticCodeResponse` objects.

Nothing changes in `app/domain/`, `app/application/`, `app/infrastructure/`, or `app/api/`. The UI is purely additive.

---

## Anti-Patterns to Avoid

**Business logic in JavaScript.** If `app.js` contains `if (batteryPercent < 20) { disableButton(); }`, that rule is now duplicated. Change the threshold in `CommandPolicy` and you must remember to change the JavaScript too.

**Calling use cases from a template.** A Jinja2 template that calls `container.lock_vehicle.execute(...)` in a template tag would make the UI a direct caller of the application layer — bypassing HTTP, bypassing the API schemas, and bypassing exception handlers.

**Putting JavaScript in the template file.** Inline `<script>` tags in `index.html` mix HTML and JavaScript, making both harder to maintain. Keep JavaScript in `app.js`.

**Serving the dashboard from a non-`/` route without adjusting static file paths.** If the dashboard were at `/dashboard`, all `href="/static/..."` references in the HTML would still resolve correctly because they are absolute. Relative paths would break.

---

## Exercises

1. Open the app at `http://localhost:8000/` in a browser. Open the browser developer tools (F12). Go to the Network tab. Click "Lock Vehicle" with a vehicle ID. Observe the HTTP POST request and the JSON response. Confirm the status code matches the scenario.

2. Add a `<p id="version">v0.1.0</p>` element to `index.html`. Pass `version="0.1.0"` to `TemplateResponse` from the Python route: `templates.TemplateResponse(request, "index.html", {"version": "0.1.0"})`. Update the template to use `{{ version }}`. Confirm the version appears in the rendered HTML.

3. Add a new `fetchAlerts(vehicleId)` function to `app.js` that calls `GET /vehicles/{vehicleId}/alerts` and prints the results to the browser console. Do not modify any Python files.

---

## Review Checklist

- [ ] I can explain why the browser is an inbound adapter.
- [ ] I know the difference between `Jinja2Templates.TemplateResponse` and `StaticFiles`.
- [ ] I understand why business rules must not be duplicated in the JavaScript layer.
- [ ] I can add a new UI section without changing any Python code.
- [ ] I know where the template and static files live in the project structure.
