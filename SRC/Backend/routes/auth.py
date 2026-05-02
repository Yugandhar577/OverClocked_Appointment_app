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


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user, _otp = await auth_service.signup(session, payload, settings.otp_ttl_seconds)
    return SignupResponse(user_id=user.id, message="otp_sent")


@router.post("/verify-otp", response_model=VerifyOtpResponse)
async def verify_otp(payload: VerifyOtpRequest, session: AsyncSession = Depends(get_db)):
    verified = await auth_service.verify_otp(session, payload.email, payload.otp)
    return VerifyOtpResponse(verified=verified)


@router.post("/resend-otp")
async def resend_otp(
    payload: ResendOtpRequest,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    await auth_service.resend_otp(session, payload.email, settings.otp_ttl_seconds)
    return {"sent": True}


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


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, session: AsyncSession = Depends(get_db)):
    await auth_service.reset_password(session, payload.token, payload.new_password)
    return {"reset": True}


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
