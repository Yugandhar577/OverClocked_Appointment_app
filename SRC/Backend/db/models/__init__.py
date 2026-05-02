"""
Backend documentation for `db/models/__init__.py`.

This model module declares database persistence structures and relationships used by SQLAlchemy.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from SRC.Backend.db.base import Base
from SRC.Backend.db.models.auth import OtpVerification, Role, User, user_roles
from SRC.Backend.db.models.organization import Organization
from SRC.Backend.db.models.booking import Appointment, AppointmentAnswer, SlotCapacityLog
from SRC.Backend.db.models.comms import AuditLog, Notification, Payment
from SRC.Backend.db.models.advanced import (
    BookingCartQuote,
    CancellationPolicy,
    CustomerPackageBalance,
    FeatureFlagOverride,
    Package,
    PricingRule,
    RecurringSeries,
    ThemeSettings,
    WaitlistEntry,
)
from SRC.Backend.db.models.scheduling import (
    AppointmentQuestion,
    AppointmentType,
    AppointmentTypeResource,
    BookingRule,
    FlexibleSlot,
    GeneratedSlot,
    Resource,
    WorkingHour,
)

__all__ = [
    "Base",
    "Organization",
    "User",
    "Role",
    "user_roles",
    "OtpVerification",
    "AppointmentType",
    "Resource",
    "AppointmentTypeResource",
    "BookingRule",
    "AppointmentQuestion",
    "WorkingHour",
    "FlexibleSlot",
    "GeneratedSlot",
    "Appointment",
    "AppointmentAnswer",
    "SlotCapacityLog",
    "Payment",
    "Notification",
    "AuditLog",
    "FeatureFlagOverride",
    "WaitlistEntry",
    "BookingCartQuote",
    "RecurringSeries",
    "Package",
    "CustomerPackageBalance",
    "CancellationPolicy",
    "PricingRule",
    "ThemeSettings",
]
