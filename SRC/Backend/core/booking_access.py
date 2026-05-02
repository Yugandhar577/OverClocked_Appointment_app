"""Aligned access rules for booking detail and payment APIs."""

from SRC.Backend.db.models import Appointment, AppointmentType, User


def _roles(actor: User) -> list[str]:
    return getattr(actor, "roles_snapshot", []) or []


def ids_equal(a, b) -> bool:
    if a is None or b is None:
        return False
    return str(a) == str(b)


def is_admin(actor: User) -> bool:
    return "admin" in _roles(actor)


def can_view_booking(actor: User | None, appointment: Appointment, appointment_type: AppointmentType) -> bool:
    if actor is None:
        return False
    if is_admin(actor):
        return True
    if ids_equal(actor.id, appointment.customer_id):
        return True
    if ids_equal(actor.id, appointment_type.organiser_id):
        return True
    return False


def can_use_payment_endpoints(actor: User, appointment: Appointment, appointment_type: AppointmentType) -> bool:
    if is_admin(actor) or ids_equal(actor.id, appointment.customer_id):
        return True
    if "organiser" in _roles(actor) and ids_equal(actor.id, appointment_type.organiser_id):
        return True
    return False
