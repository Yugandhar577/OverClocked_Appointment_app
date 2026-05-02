import asyncio

from sqlalchemy import select

from SRC.Backend.db.models import AppointmentType
from SRC.Backend.db.session import async_session_factory
from SRC.Backend.services.slot_generation_service import regenerate


async def main() -> None:
    total = 0
    async with async_session_factory() as session:
        ids = (await session.execute(select(AppointmentType.id).where(AppointmentType.is_published.is_(True)))).scalars().all()
        for appointment_type_id in ids:
            total += await regenerate(session, appointment_type_id)
    print(f"Generated {total} slots.")


if __name__ == "__main__":
    asyncio.run(main())
