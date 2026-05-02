"""
Backend documentation for `schemas/auth.py`.

This schema module defines request/response contracts used by FastAPI and the frontend TypeScript client.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Backend note: API request contract accepted from the frontend.
class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: str
    password: str = Field(min_length=8)
    timezone: str = "UTC"


# Backend note: API response contract sent back to the frontend.
class SignupResponse(BaseModel):
    user_id: UUID
    message: str


# Backend note: API request contract accepted from the frontend.
class VerifyOtpRequest(BaseModel):
    email: str
    otp: str = Field(min_length=4, max_length=8)


# Backend note: API response contract sent back to the frontend.
class VerifyOtpResponse(BaseModel):
    verified: bool


# Backend note: API request contract accepted from the frontend.
class ResendOtpRequest(BaseModel):
    email: str


# Backend note: API request contract accepted from the frontend.
class LoginRequest(BaseModel):
    email: str
    password: str


# Backend note: Groups related backend data or behavior for a single domain concept.
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


# Backend note: API response contract sent back to the frontend.
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# Backend note: API request contract accepted from the frontend.
class ForgotPasswordRequest(BaseModel):
    email: str


# Backend note: API request contract accepted from the frontend.
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


# Backend note: Input contract used when updating a backend resource.
class MeUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    timezone: str | None = None
