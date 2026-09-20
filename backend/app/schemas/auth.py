from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.DONOR


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    full_name: str
    role: UserRole


class LoginResponse(BaseModel):
    # Depending on role, it might be a direct token OR require OTP
    requires_otp: bool
    email: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: Optional[int] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ResendOTPRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True
