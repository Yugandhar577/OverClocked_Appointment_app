import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from SRC.Backend.config import get_settings
from SRC.Backend.core.errors import register_exception_handlers
from SRC.Backend.db.session import engine
from SRC.Backend.routes import admin, advanced, appointment_types, auth, bookings, health, organizations
from SRC.Backend.routes import organiser_settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="UTC")


async def _run_reminder_dispatcher() -> None:
    from SRC.Backend.jobs.reminder_dispatcher import enqueue_due_reminders
    try:
        await enqueue_due_reminders()
    except Exception:
        logger.exception("reminder_dispatcher job failed")


async def _run_notification_dispatcher() -> None:
    from SRC.Backend.jobs.notification_dispatcher import dispatch_queued_notifications
    try:
        await dispatch_queued_notifications()
    except Exception:
        logger.exception("notification_dispatcher job failed")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    scheduler.add_job(
        _run_reminder_dispatcher,
        "interval",
        minutes=5,
        id="reminder_dispatcher",
        max_instances=1,
        misfire_grace_time=60,
    )
    scheduler.add_job(
        _run_notification_dispatcher,
        "interval",
        minutes=1,
        id="notification_dispatcher",
        max_instances=1,
        misfire_grace_time=30,
    )
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
    await engine.dispose()


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
    app.include_router(organiser_settings.router, prefix="/api/v1")
    return app


app = create_app()
