"""
Backend documentation for `main.py`.

This backend module participates in the appointment platform and is documented to make future changes safer.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from SRC.Backend.config import get_settings
from SRC.Backend.core.errors import register_exception_handlers
from SRC.Backend.db.session import engine
from SRC.Backend.routes import admin, advanced, appointment_types, auth, bookings, health, organizations


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await engine.dispose()

# Function explanation:
# `lifespan` is an async context manager used by FastAPI to run code during
# application startup/shutdown. It yields control to the app runtime and
# ensures the database engine is disposed when the app shuts down to free
# resources and close connections cleanly.
#
# Alternative (commented): use FastAPI `on_event` handlers instead of an
# asynccontextmanager. This separates startup and shutdown into explicit
# functions and can be clearer when multiple startup tasks are needed.
#
# async def on_startup() -> None:
#     # e.g., initialize background tasks, warm caches, or verify DB
#     pass
#
# async def on_shutdown() -> None:
#     await engine.dispose()
#
# app = FastAPI()
# app.add_event_handler("startup", on_startup)
# app.add_event_handler("shutdown", on_shutdown)


# Backend note: Creates a new domain record after validation and keeps side effects scoped to this workflow.
def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(appointment_types.router, prefix="/api/v1")
    app.include_router(bookings.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")
    app.include_router(organizations.router, prefix="/api/v1")
    app.include_router(advanced.router, prefix="/api/v1")
    return app


# Function explanation:
# `create_app` is an application factory: it constructs and configures a
# `FastAPI` instance, registers middleware, exception handlers and route
# groups. Using a factory makes the app easier to test and configure.
#
# Alternative (commented): accept a `settings` parameter so tests can
# inject different configurations without patching the global `get_settings`.
#
# def create_app_with_settings(settings) -> FastAPI:
#     app = FastAPI(title=settings.app_name, lifespan=lifespan)
#     app.add_middleware(...)
#     register_exception_handlers(app)
#     return app


app = create_app()
