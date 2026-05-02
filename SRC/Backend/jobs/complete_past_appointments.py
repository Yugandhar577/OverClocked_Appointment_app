import asyncio

from sqlalchemy import select

from SRC.Backend.core.time import utcnow
from SRC.Backend.db.models import Appointment, GeneratedSlot
from SRC.Backend.db.session import async_session_factory
from SRC.Backend.services.appointment_service import transition


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
