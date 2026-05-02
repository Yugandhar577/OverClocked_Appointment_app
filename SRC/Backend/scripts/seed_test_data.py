import asyncio
from datetime import time
from types import SimpleNamespace

from sqlalchemy import insert, select, text

from SRC.Backend.core.security import hash_password
from SRC.Backend.db.models import (
    AppointmentType,
    AppointmentTypeResource,
    BookingRule,
    GeneratedSlot,
    Resource,
    Role,
    User,
    WorkingHour,
    user_roles,
)
from SRC.Backend.db.session import async_session_factory
from SRC.Backend.schemas.bookings import BookingCreate, CustomerInfoIn, IntakeAnswerIn
from SRC.Backend.services import booking_service, slot_generation_service
from SRC.Backend.services.auth_service import ensure_default_roles


async def create_user(session, full_name: str, email: str, password: str, roles: list[str]) -> User:
    user = User(
        full_name=full_name,
        email=email,
        password_hash=hash_password(password),
        is_verified=True,
        is_active=True,
        timezone="Asia/Kolkata",
    )
    session.add(user)
    await session.flush()
    role_rows = (await session.execute(select(Role).where(Role.name.in_(roles)))).scalars().all()
    for role in role_rows:
        await session.execute(insert(user_roles).values(user_id=user.id, role_id=role.id))
    user.roles_snapshot = roles
    return user


async def main() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            for table in [
                "audit_logs",
                "notifications",
                "payments",
                "slot_capacity_log",
                "appointment_answers",
                "appointments",
                "generated_slots",
                "flexible_slots",
                "working_hours",
                "appointment_questions",
                "booking_rules",
                "appointment_type_resources",
                "resources",
                "appointment_types",
                "otp_verifications",
                "user_roles",
                "users",
            ]:
                await session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
        async with session.begin():
            await ensure_default_roles(session)
            admin = await create_user(session, "Admin User", "admin@test.local", "Admin123!", ["admin"])
            org1 = await create_user(session, "Organiser One", "org1@test.local", "Organiser123!", ["organiser"])
            org2 = await create_user(session, "Organiser Two", "org2@test.local", "Organiser123!", ["organiser"])
            customers = [
                await create_user(session, f"Customer {index}", f"cust{index}@test.local", "Customer123!", ["customer"])
                for index in range(1, 6)
            ]
            customer_refs = [
                SimpleNamespace(id=customer.id, full_name=customer.full_name, email=customer.email, phone=customer.phone)
                for customer in customers
            ]

            consultation = AppointmentType(
                organiser_id=org1.id,
                title="30-min Consultation",
                description="Focused consultation slot for customer demos.",
                duration_minutes=30,
                timezone="Asia/Kolkata",
                preset_type="meeting",
                resource_type="user",
                share_token="consultation-demo-share",
                is_published=True,
                manage_capacity=True,
                max_capacity=4,
                cancel_before_minutes=60,
                reschedule_before_minutes=60,
                future_days_limit=14,
                venue="Room 201, VIT Pune",
            )
            strategy = AppointmentType(
                organiser_id=org1.id,
                title="Strategy Session",
                description="Paid one-seat strategy discussion.",
                duration_minutes=60,
                timezone="Asia/Kolkata",
                preset_type="strategy",
                resource_type="user",
                share_token="strategy-demo-share",
                is_published=True,
                is_paid=True,
                price=500,
                requires_confirmation=True,
                manage_capacity=True,
                max_capacity=1,
                cancel_before_minutes=60,
                reschedule_before_minutes=60,
                future_days_limit=14,
                venue="Video call",
            )
            session.add_all([consultation, strategy])
            await session.flush()

            dr_sharma = Resource(organiser_id=org1.id, name="Dr. Sharma", resource_type="human", capacity=4, timezone="Asia/Kolkata")
            coach = Resource(organiser_id=org1.id, name="Strategy Coach", resource_type="human", capacity=1, timezone="Asia/Kolkata")
            session.add_all([dr_sharma, coach])
            await session.flush()
            session.add_all(
                [
                    AppointmentTypeResource(appointment_type_id=consultation.id, resource_id=dr_sharma.id, priority=1),
                    AppointmentTypeResource(appointment_type_id=strategy.id, resource_id=coach.id, priority=1),
                    BookingRule(appointment_type_id=consultation.id, max_bookings_per_slot=4),
                    BookingRule(appointment_type_id=strategy.id, max_bookings_per_slot=1),
                ]
            )
            for day in range(5):
                session.add(
                    WorkingHour(
                        appointment_type_id=consultation.id,
                        day_of_week=day,
                        start_time=time(9, 0),
                        end_time=time(17, 0),
                    )
                )
            for day in [1, 3]:
                session.add(
                    WorkingHour(
                        appointment_type_id=strategy.id,
                        day_of_week=day,
                        start_time=time(10, 0),
                        end_time=time(14, 0),
                    )
                )

        consultation_id = consultation.id
        strategy_id = strategy.id
        await slot_generation_service.regenerate(session, consultation_id)
        await slot_generation_service.regenerate(session, strategy_id)

        consultation_slots = (
            await session.execute(
                select(GeneratedSlot)
                .where(GeneratedSlot.appointment_type_id == consultation_id)
                .order_by(GeneratedSlot.start_datetime.asc())
            )
        ).scalars().all()
        strategy_slots = (
            await session.execute(
                select(GeneratedSlot)
                .where(GeneratedSlot.appointment_type_id == strategy_id)
                .order_by(GeneratedSlot.start_datetime.asc())
            )
        ).scalars().all()

        consultation_slot_refs = [(slot.id, slot.resource_id) for slot in consultation_slots]
        strategy_slot_refs = [(slot.id, slot.resource_id) for slot in strategy_slots]
        await session.rollback()

        if consultation_slot_refs:
            await booking_service.create(
                session,
                BookingCreate(
                    appointment_type_id=consultation_id,
                    slot_id=consultation_slot_refs[0][0],
                    resource_id=consultation_slot_refs[0][1],
                    people_count=1,
                    customer_info=CustomerInfoIn(full_name="Customer 1", email="cust1@test.local"),
                    answers=[],
                ),
                customer_refs[0],
            )
            appt, *_ = await booking_service.create(
                session,
                BookingCreate(
                    appointment_type_id=consultation_id,
                    slot_id=consultation_slot_refs[1][0],
                    resource_id=consultation_slot_refs[1][1],
                    people_count=1,
                    customer_info=CustomerInfoIn(full_name="Customer 3", email="cust3@test.local"),
                    answers=[],
                ),
                customer_refs[2],
            )
            await booking_service.cancel(session, appt.id, customer_refs[2], "seed cancelled", bypass_window=True)

        if strategy_slot_refs:
            await booking_service.create(
                session,
                BookingCreate(
                    appointment_type_id=strategy_id,
                    slot_id=strategy_slot_refs[0][0],
                    resource_id=strategy_slot_refs[0][1],
                    people_count=1,
                    customer_info=CustomerInfoIn(full_name="Customer 2", email="cust2@test.local"),
                    answers=[],
                ),
                customer_refs[1],
            )

    print("Seeded demo data.")
    print("admin@test.local / Admin123!")
    print("org1@test.local / Organiser123!")
    print("cust1@test.local / Customer123!")


if __name__ == "__main__":
    asyncio.run(main())
