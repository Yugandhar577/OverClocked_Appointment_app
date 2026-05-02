from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 400
    detail: str | dict = "app_error"

    def __init__(self, detail: str | dict | None = None):
        if detail is not None:
            self.detail = detail


class InvalidCredentialsError(AppError):
    status_code = 401
    detail = "invalid_credentials"


class AccountUnverifiedError(AppError):
    status_code = 403
    detail = "account_unverified"


class AccountDisabledError(AppError):
    status_code = 403
    detail = "account_disabled"


class OtpExpiredError(AppError):
    status_code = 410
    detail = "otp_expired"


class EmailExistsError(AppError):
    status_code = 409
    detail = "email_exists"


class NotOwnerError(AppError):
    status_code = 403
    detail = "not_owner"


class RoleRequiredError(AppError):
    status_code = 403

    def __init__(self, required: str):
        super().__init__({"detail": "role_required", "required": required})


class SlotUnavailableError(AppError):
    status_code = 409
    detail = "slot_unavailable"


class CapacityExceededError(AppError):
    status_code = 409
    detail = "capacity_exceeded"


class IntakeAnswerMissingError(AppError):
    status_code = 422

    def __init__(self, question_id):
        super().__init__({"detail": "intake_answer_missing", "question_id": str(question_id)})


class CancelWindowClosedError(AppError):
    status_code = 409
    detail = "cancel_window_closed"


class RescheduleWindowClosedError(AppError):
    status_code = 409
    detail = "reschedule_window_closed"


class SameSlotRescheduleError(AppError):
    status_code = 422
    detail = "same_slot_reschedule"


class InvalidTransitionError(AppError):
    status_code = 409

    def __init__(self, current: str, target: str):
        super().__init__({"detail": "invalid_transition", "from": current, "to": target})


class ConfigIncompleteError(AppError):
    status_code = 422

    def __init__(self, missing: list[str]):
        super().__init__({"detail": "config_incomplete", "missing": missing})


class LastAdminProtectedError(AppError):
    status_code = 422
    detail = "last_admin_protected"


class SelfDeactivationForbiddenError(AppError):
    status_code = 422
    detail = "self_deactivation_forbidden"


class NotFoundError(AppError):
    status_code = 404

    def __init__(self, resource: str = "resource"):
        super().__init__({"detail": "not_found", "resource": resource})


class OrganizationDomainExistsError(AppError):
    status_code = 409
    detail = "organization_domain_exists"


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
