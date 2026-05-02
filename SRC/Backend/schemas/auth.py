from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: str
    password: str = Field(min_length=8)
    timezone: str = "UTC"


class SignupResponse(BaseModel):
    user_id: UUID
    message: str


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str = Field(min_length=4, max_length=8)


class VerifyOtpResponse(BaseModel):
    verified: bool


class ResendOtpRequest(BaseModel):
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    roles: list[str]
    is_verified: bool
    is_active: bool
    phone: str | None = None
    timezone: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class MeUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    timezone: str | None = None
