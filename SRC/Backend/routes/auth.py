"""
Backend documentation for `routes/auth.py`.

This route module keeps HTTP concerns thin: validate inputs, call service-layer logic, and return typed API responses.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.config import Settings, get_settings
from SRC.Backend.core.deps import get_current_user
from SRC.Backend.db.models import User
from SRC.Backend.db.session import get_db
from SRC.Backend.schemas.auth import (
    ForgotPasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    MeUpdateRequest,
    ResendOtpRequest,
    ResetPasswordRequest,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    UserOut,
    VerifyOtpRequest,
    VerifyOtpResponse,
)
from SRC.Backend.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user, _otp = await auth_service.signup(session, payload, settings.otp_ttl_seconds)
    return SignupResponse(user_id=user.id, message="otp_sent")


# Explanation:
# `signup` receives a signup payload, calls `auth_service.signup` to create
# the user and send an OTP, then returns a minimal response indicating the
# OTP was sent. The heavy lifting is delegated to the service layer.
#
# Alternative (commented, directly below function as requested):
# Implement synchronous signup flow that returns created user info and
# performs OTP sending in a background task rather than awaiting it.
#
# @router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
# async def signup_background(payload: SignupRequest, background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_db)):
#     user, _ = await auth_service.create_user_db(session, payload)
#     background_tasks.add_task(auth_service.send_otp, user.email)
#     return SignupResponse(user_id=user.id, message="otp_queued")


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.post("/verify-otp", response_model=VerifyOtpResponse)
async def verify_otp(payload: VerifyOtpRequest, session: AsyncSession = Depends(get_db)):
    verified = await auth_service.verify_otp(session, payload.email, payload.otp)
    return VerifyOtpResponse(verified=verified)


# Explanation:
# `verify_otp` delegates OTP validation to `auth_service.verify_otp` and
# returns whether verification succeeded. Keeping verification in service
# layer centralizes token logic.
#
# Alternative (commented): accept both email+otp and token-based verify
# endpoints to support different client flows (e.g., tokenized links).
#
# @router.post("/verify-otp", response_model=VerifyOtpResponse)
# async def verify_otp_token(payload: VerifyOtpRequest, token: str = Query(None), session: AsyncSession = Depends(get_db)):
#     if token:
#         verified = await auth_service.verify_otp_token(session, token)
#     else:
#         verified = await auth_service.verify_otp(session, payload.email, payload.otp)
#     return VerifyOtpResponse(verified=verified)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.post("/resend-otp")
async def resend_otp(
    payload: ResendOtpRequest,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    await auth_service.resend_otp(session, payload.email, settings.otp_ttl_seconds)
    return {"sent": True}


# Explanation:
# `resend_otp` calls the service to resend a one-time passcode. Rate
# limiting should be handled in the service or via API gateway to prevent
# abuse.
#
# Alternative (commented): return a `retry_after` header or limited
# response to indicate when the next OTP can be requested.
#
# @router.post("/resend-otp")
# async def resend_otp_rate_limited(...):
#     # check rate limit
#     await auth_service.resend_otp(...)
#     return Response(status_code=202)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db)):
    token, user, roles = await auth_service.login(session, payload.email, payload.password)
    return TokenResponse(
        access_token=token,
        user=UserOut(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            roles=roles,
            is_verified=user.is_verified,
            is_active=user.is_active,
            phone=user.phone,
            timezone=user.timezone,
        ),
    )


# Explanation:
# `login` authenticates credentials via `auth_service.login`, receives
# an access token and user details, and returns a typed token response.
#
# Alternative (commented): implement separate endpoints for password and
# OTP-based login to keep concerns separated and simplified.
#
# @router.post("/login/otp", response_model=TokenResponse)
# async def login_with_otp(...):
#     token = await auth_service.login_with_otp(...)
#     return TokenResponse(access_token=token, user=...)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.post("/google", response_model=TokenResponse)
async def google_auth(
    payload: GoogleAuthRequest,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    token, user, roles = await auth_service.google_login(session, payload.id_token, settings.google_client_id)
    return TokenResponse(
        access_token=token,
        user=UserOut(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            roles=roles,
            is_verified=user.is_verified,
            is_active=user.is_active,
            phone=user.phone,
            timezone=user.timezone,
        ),
    )


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, session: AsyncSession = Depends(get_db)):
    await auth_service.forgot_password(session, payload.email)
    return {"sent": True}


# Explanation:
# `forgot_password` initiates the reset flow via the service layer. The
# service is responsible for generating tokens and emailing the user.
#
# Alternative (commented): return a generic 202 Accepted without exposing
# whether an account with the email exists, to avoid account enumeration.
#
# @router.post("/forgot-password")
# async def forgot_password_generic(...):
#     await auth_service.forgot_password(...)
#     return Response(status_code=202)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, session: AsyncSession = Depends(get_db)):
    await auth_service.reset_password(session, payload.token, payload.new_password)
    return {"reset": True}


# Explanation:
# `reset_password` validates and applies the new password via service
# logic. Services should ensure tokens are single-use and properly revoked.
#
# Alternative (commented): accept both token and OTP-based resets; use
# DB-backed single-use tokens for extra security.
#
# @router.post("/reset-password")
# async def reset_password_db_backed(...):
#     await auth_service.reset_password_db(session, ...)
#     return {"reset": True}


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/me", response_model=UserOut)
async def auth_me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        roles=getattr(current_user, "roles_snapshot", []),
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
        phone=current_user.phone,
        timezone=current_user.timezone,
    )


# Explanation:
# `auth_me` returns the authenticated user's profile using `get_current_user`.
# It's intentionally thin and returns a serializable `UserOut` schema.
#
# Alternative (commented): return additional computed data (e.g.,
# permissions, feature flags) by attaching them in the service layer.
#
# @router.get("/me/with-permissions")
# async def auth_me_with_permissions(current_user: User = Depends(get_current_user)):
#     permissions = compute_permissions(current_user)
#     return {"user": UserOut(...), "permissions": permissions}


# Backend note: Updates an existing domain record in place while preserving unrelated data.
@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: MeUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    async with session.begin():
        user = await session.get(User, current_user.id)
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.phone is not None:
            user.phone = payload.phone
        if payload.timezone is not None:
            user.timezone = payload.timezone
    roles = getattr(current_user, "roles_snapshot", [])
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=roles,
        is_verified=user.is_verified,
        is_active=user.is_active,
        phone=user.phone,
        timezone=user.timezone,
    )


# Explanation:
# `update_me` updates allowed profile fields inside a transaction and
# returns the updated `UserOut` model. It forbids changing sensitive
# attributes like email/password directly in this endpoint.
#
# Alternative (commented): implement PATCH merge semantics using `dict`
# merging and validation helpers or allow partial updates via JSON Patch.
#
# @router.patch("/me")
# async def update_me_partial(payload: MeUpdateRequest, ...):
#     # apply patch operations here
#     return UserOut(...)
