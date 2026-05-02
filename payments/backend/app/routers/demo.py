from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Appointment, AppointmentType, GeneratedSlot, Payment, User
from app.schemas import DemoSeedResponse

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/reset-and-seed", response_model=DemoSeedResponse)
def reset_and_seed(db: Session = Depends(get_db)) -> DemoSeedResponse:
    """Wipes payment-related tables and inserts one paid appointment ready for checkout (test only)."""
    db.execute(delete(Payment))
    db.execute(delete(Appointment))
    db.execute(delete(GeneratedSlot))
    db.execute(delete(AppointmentType))
    db.execute(delete(User))

    organiser = User(
        full_name="Demo Organiser",
        email="organiser@demo.local",
        password_hash="bcrypt-demo-not-used",
        phone="+919999999001",
    )
    customer = User(
        full_name="Demo Customer",
        email="customer@demo.local",
        password_hash="bcrypt-demo-not-used",
        phone="+919999999002",
    )
    db.add_all([organiser, customer])
    db.flush()

    appt_type = AppointmentType(
        organiser_id=organiser.id,
        title="Paid consultation (demo)",
        description="Hackathon demo — advance payment via Razorpay Standard Checkout.",
        duration_minutes=30,
        is_published=True,
        is_paid=True,
        price=Decimal("10.00"),
        currency="INR",
    )
    db.add(appt_type)
    db.flush()

    start = datetime.now(timezone.utc) + timedelta(days=1)
    end = start + timedelta(minutes=30)
    slot = GeneratedSlot(
        appointment_type_id=appt_type.id,
        start_datetime=start,
        end_datetime=end,
        max_capacity=1,
        booked_count=0,
        is_blocked=False,
        source="weekly",
    )
    db.add(slot)
    db.flush()

    appointment = Appointment(
        appointment_type_id=appt_type.id,
        slot_id=slot.id,
        customer_id=customer.id,
        status="pending",
        people_count=1,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return DemoSeedResponse(
        organiser_id=organiser.id,
        customer_id=customer.id,
        appointment_type_id=appt_type.id,
        slot_id=slot.id,
        appointment_id=appointment.id,
        message="Use POST /api/payments/initiate with appointment_id, then complete Razorpay checkout.",
    )


@router.get("/appointment/{appointment_id}")
def get_appointment_stub(appointment_id: UUID, db: Session = Depends(get_db)) -> dict:
    row = db.get(Appointment, appointment_id)
    if not row:
        return {"error": "not_found"}
    return {
        "id": str(row.id),
        "status": row.status,
        "appointment_type_id": str(row.appointment_type_id),
        "customer_id": str(row.customer_id),
    }
