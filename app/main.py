from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from app.composition.container import Container
from app.api.exception_handlers import domain_exception_handler, generic_exception_handler
from app.domain.errors import DomainError
from app.api.routes import health, ui, commands, telemetry, eligibility, alerts, trips, maintenance, diagnostics


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = Container()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Automotive Vehicle Command & Telematics Service",
        description="A hexagonal architecture learning project using FastAPI",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_exception_handler(DomainError, domain_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    static_dir = os.path.join(os.path.dirname(__file__), "ui", "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    app.include_router(health.router)
    app.include_router(ui.router)
    app.include_router(commands.router)
    app.include_router(telemetry.router)
    app.include_router(eligibility.router)
    app.include_router(alerts.router)
    app.include_router(trips.router)
    app.include_router(maintenance.router)
    app.include_router(diagnostics.router)

    return app
