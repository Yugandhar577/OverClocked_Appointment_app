"""
Backend documentation for `core/errors.py`.

This core utility module centralizes shared backend behavior such as security, dependency injection, errors, or time handling.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# Backend note: Groups related backend data or behavior for a single domain concept.
class AppError(Exception):
    status_code = 400
    detail: str | dict = "app_error"

    def __init__(self, detail: str | dict | None = None):
        if detail is not None:
            self.detail = detail


# Backend note: Groups related backend data or behavior for a single domain concept.
class InvalidCredentialsError(AppError):
    status_code = 401
    detail = "invalid_credentials"


# Backend note: Groups related backend data or behavior for a single domain concept.
class AccountUnverifiedError(AppError):
    status_code = 403
    detail = "account_unverified"


# Backend note: Groups related backend data or behavior for a single domain concept.
class AccountDisabledError(AppError):
    status_code = 403
    detail = "account_disabled"


# Backend note: Groups related backend data or behavior for a single domain concept.
class OtpExpiredError(AppError):
    status_code = 410
    detail = "otp_expired"


# Backend note: Groups related backend data or behavior for a single domain concept.
class EmailExistsError(AppError):
    status_code = 409
    detail = "email_exists"


# Backend note: Groups related backend data or behavior for a single domain concept.
class NotOwnerError(AppError):
    status_code = 403
    detail = "not_owner"


# Backend note: Groups related backend data or behavior for a single domain concept.
class RoleRequiredError(AppError):
    status_code = 403

    def __init__(self, required: str):
        super().__init__({"detail": "role_required", "required": required})


# Backend note: Groups related backend data or behavior for a single domain concept.
class SlotUnavailableError(AppError):
    status_code = 409
    detail = "slot_unavailable"


# Backend note: Groups related backend data or behavior for a single domain concept.
class CapacityExceededError(AppError):
    status_code = 409
    detail = "capacity_exceeded"


# Backend note: Groups related backend data or behavior for a single domain concept.
class BookingInProgressError(AppError):
    status_code = 409
    detail = "booking_in_progress"


# Backend note: Groups related backend data or behavior for a single domain concept.
class IntakeAnswerMissingError(AppError):
    status_code = 422

    def __init__(self, question_id):
        super().__init__({"detail": "intake_answer_missing", "question_id": str(question_id)})


# Backend note: Groups related backend data or behavior for a single domain concept.
class IntakeAnswerInvalidError(AppError):
    status_code = 422

    def __init__(self, question_id, message: str):
        super().__init__({"detail": "intake_answer_invalid", "question_id": str(question_id), "message": message})


# Backend note: Groups related backend data or behavior for a single domain concept.
class CancelWindowClosedError(AppError):
    status_code = 409
    detail = "cancel_window_closed"


# Backend note: Groups related backend data or behavior for a single domain concept.
class RescheduleWindowClosedError(AppError):
    status_code = 409
    detail = "reschedule_window_closed"


# Backend note: Groups related backend data or behavior for a single domain concept.
class SameSlotRescheduleError(AppError):
    status_code = 422
    detail = "same_slot_reschedule"


# Backend note: Groups related backend data or behavior for a single domain concept.
class InvalidTransitionError(AppError):
    status_code = 409

    def __init__(self, current: str, target: str):
        super().__init__({"detail": "invalid_transition", "from": current, "to": target})


# Backend note: Groups related backend data or behavior for a single domain concept.
class ConfigIncompleteError(AppError):
    status_code = 422

    def __init__(self, missing: list[str]):
        super().__init__({"detail": "config_incomplete", "missing": missing})


# Backend note: Groups related backend data or behavior for a single domain concept.
class LastAdminProtectedError(AppError):
    status_code = 422
    detail = "last_admin_protected"


# Backend note: Groups related backend data or behavior for a single domain concept.
class SelfDeactivationForbiddenError(AppError):
    status_code = 422
    detail = "self_deactivation_forbidden"


# Backend note: Groups related backend data or behavior for a single domain concept.
class NotFoundError(AppError):
    status_code = 404

    def __init__(self, resource: str = "resource"):
        super().__init__({"detail": "not_found", "resource": resource})


# Backend note: Groups related backend data or behavior for a single domain concept.
class OrganizationDomainExistsError(AppError):
    status_code = 409
    detail = "organization_domain_exists"


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.


class GoogleAuthError(AppError):
    status_code = 401
    detail = "google_auth_failed"


class GoogleNotConfiguredError(AppError):
    status_code = 501
    detail = "google_not_configured"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError):
        if isinstance(exc.detail, dict):
            content = exc.detail
        else:
            content = {"detail": exc.detail}
        return JSONResponse(status_code=exc.status_code, content=content)


    # Function explanation:
    # `register_exception_handlers` attaches a FastAPI exception handler for the
    # application's `AppError` base class. When any `AppError` is raised in route
    # or service code, this handler converts it into a consistent JSON response
    # using the error's `status_code` and `detail` payload.
    #
    # Alternative (commented): implement a middleware that intercepts all
    # exceptions and maps known types to responses. Middleware can centralize
    # logging, error transformation, and metrics, but exception handlers are
    # generally preferable for HTTP-layer error mapping in FastAPI.
    #
    # from starlette.middleware.base import BaseHTTPMiddleware
    #
    # class AppErrorMiddleware(BaseHTTPMiddleware):
    #     async def dispatch(self, request, call_next):
    #         try:
    #             return await call_next(request)
    #         except AppError as exc:
    #             if isinstance(exc.detail, dict):
    #                 content = exc.detail
    #             else:
    #                 content = {"detail": exc.detail}
    #             return JSONResponse(status_code=exc.status_code, content=content)
