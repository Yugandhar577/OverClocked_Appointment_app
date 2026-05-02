"""
Backend documentation for `jobs/complete_past_appointments.py`.

This job module is intended for repeatable background or maintenance tasks that operate outside request/response flow.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

import asyncio

from sqlalchemy import select

from SRC.Backend.core.time import utcnow
from SRC.Backend.db.models import Appointment, GeneratedSlot
from SRC.Backend.db.session import async_session_factory
from SRC.Backend.services.appointment_service import transition


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def main() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            rows = (
                await session.execute(
                    select(Appointment)
                    .join(GeneratedSlot, GeneratedSlot.id == Appointment.slot_id)
                    .where(Appointment.status == "confirmed", GeneratedSlot.end_datetime < utcnow())
                )
            ).scalars().all()
            for appointment in rows:
                await transition(session, appointment.id, "completed", None, "cron_complete")
    print(f"Completed {len(rows)} appointments.")


if __name__ == "__main__":
    asyncio.run(main())
