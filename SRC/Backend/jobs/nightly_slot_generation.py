"""
Backend documentation for `jobs/nightly_slot_generation.py`.

This job module is intended for repeatable background or maintenance tasks that operate outside request/response flow.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

import asyncio

from sqlalchemy import select

from SRC.Backend.db.models import AppointmentType
from SRC.Backend.db.session import async_session_factory
from SRC.Backend.services.slot_generation_service import regenerate


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def main() -> None:
    total = 0
    async with async_session_factory() as session:
        ids = (await session.execute(select(AppointmentType.id).where(AppointmentType.is_published.is_(True)))).scalars().all()
        for appointment_type_id in ids:
            total += await regenerate(session, appointment_type_id)
    print(f"Generated {total} slots.")


if __name__ == "__main__":
    asyncio.run(main())
