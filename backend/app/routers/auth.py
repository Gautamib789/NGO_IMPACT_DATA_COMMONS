import random
import string
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.otp import OtpCode, OTPPurpose
from app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    LoginResponse, VerifyOTPRequest, ResendOTPRequest,
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token
from app.dependencies import get_current_user
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


def is_user_locked(db: Session, user_id: int, purpose: OTPPurpose) -> bool:
    # Check if there is an OTP for this purpose with >= 5 attempts in the last 15 mins
    limit_time = datetime.utcnow() - timedelta(minutes=15)
    recent_failed_otp = db.query(OtpCode).filter(
        OtpCode.user_id == user_id,
        OtpCode.purpose == purpose,
        OtpCode.attempt_count >= 5,
        OtpCode.created_at >= limit_time
    ).first()
    return bool(recent_failed_otp)


def lock_user(db: Session, otp_code: OtpCode):
    otp_code.attempt_count += 1
    db.commit()


from app.models.ngo import NGODetail, NGOStatus

@router.post("/register", response_model=TokenResponse)
def register_user(user_in: UserRegister, db: Session = Depends(get_db)):
    clean_email = user_in.email.strip().lower()
    existing_user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(
        email=clean_email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if new_user.role == UserRole.NGO:
        ngo = NGODetail(
            user_id=new_user.id,
            org_name=new_user.full_name or "NGO Organization",
            registration_number=f"REG-{new_user.id:04d}",
            tax_id=f"TAX-{new_user.id:04d}",
            category="General Social Welfare",
            status=NGOStatus.PENDING,
            doc_completeness_score=30.0,
            transparency_score=50.0
        )
        db.add(ngo)
        db.commit()

    token = create_access_token(subject=new_user.id, role=new_user.role.value)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role
    )


@router.post("/login", response_model=LoginResponse)
def login_user(user_in: UserLogin, db: Session = Depends(get_db)):
    clean_email = user_in.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is inactive"
        )

    if user.role == UserRole.DONOR:
        token = create_access_token(subject=user.id, role=user.role.value, otp_verified=True)
        return LoginResponse(
            requires_otp=False,
            email=user.email,
            access_token=token,
            user_id=user.id,
            full_name=user.full_name,
            role=user.role
        )

    # ADMIN and NGO require 2FA Email OTP Verification
    if is_user_locked(db, user.id, OTPPurpose.LOGIN):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account is temporarily locked due to too many failed OTP attempts. Try again in 15 minutes."
        )

    # Invalidate previous unused LOGIN OTPs
    db.query(OtpCode).filter(
        OtpCode.user_id == user.id,
        OtpCode.purpose == OTPPurpose.LOGIN,
        OtpCode.used == False
    ).update({"used": True})

    otp = generate_otp()
    otp_hash = get_password_hash(otp)
    otp_code = OtpCode(
        user_id=user.id,
        purpose=OTPPurpose.LOGIN,
        hashed_otp=otp_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(otp_code)
    db.commit()

    EmailService.send_login_otp(user.email, otp)

    token = create_access_token(subject=user.id, role=user.role.value, otp_verified=False)
    
    return LoginResponse(
        requires_otp=True,
        email=user.email,
        access_token=token,
        user_id=user.id,
        full_name=user.full_name,
        role=user.role
    )

@router.post("/generate-role-otp")
def generate_role_otp(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in [UserRole.ADMIN, UserRole.NGO]:
        raise HTTPException(status_code=400, detail="OTP generation is only available for NGO and Admin roles.")

    if is_user_locked(db, current_user.id, OTPPurpose.LOGIN):
        raise HTTPException(status_code=429, detail="Account is temporarily locked due to too many failed OTP attempts. Try again in 15 minutes.")

    # Invalidate old unused OTPs
    db.query(OtpCode).filter(OtpCode.user_id == current_user.id, OtpCode.purpose == OTPPurpose.LOGIN, OtpCode.used == False).update({"used": True})
    
    otp = generate_otp()
    otp_hash = get_password_hash(otp)
    otp_code = OtpCode(
        user_id=current_user.id,
        purpose=OTPPurpose.LOGIN,
        hashed_otp=otp_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(otp_code)
    db.commit()

    delivery_res = EmailService.send_login_otp(current_user.email, otp)
    
    return {
        "message": "OTP generated successfully",
        "email": current_user.email,
        "dev_mode": delivery_res.get("dev_mode", False),
        "delivered": delivery_res.get("delivered", False),
        "dev_note": delivery_res.get("message") if delivery_res.get("dev_mode") else None
    }


@router.post("/verify-login-otp", response_model=TokenResponse)
def verify_login_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Verify the 6-digit login OTP.
    Does NOT require a Bearer token — the email+OTP pair is the credential at this step.
    A valid fully-authenticated JWT is issued ONLY after successful OTP verification.
    """
    clean_email = req.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Unable to verify the authentication session. Please sign in again.")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is inactive.")

    if is_user_locked(db, user.id, OTPPurpose.LOGIN):
        raise HTTPException(
            status_code=429,
            detail="Account is temporarily locked due to too many failed attempts. Please try again in 15 minutes."
        )

    otp_code = db.query(OtpCode).filter(
        OtpCode.user_id == user.id,
        OtpCode.purpose == OTPPurpose.LOGIN,
        OtpCode.used == False
    ).order_by(OtpCode.created_at.desc()).first()

    if not otp_code:
        raise HTTPException(
            status_code=400,
            detail="Verification session expired. Please sign in again to request a new code."
        )

    if otp_code.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Verification code expired. Please request a new code."
        )

    if not verify_password(req.otp, otp_code.hashed_otp):
        lock_user(db, otp_code)
        raise HTTPException(status_code=401, detail="Incorrect verification code.")

    otp_code.used = True
    db.commit()

    # Issue the final authenticated JWT with otp_verified=True
    token = create_access_token(subject=user.id, role=user.role.value, otp_verified=True)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )


@router.post("/resend-login-otp")
def resend_login_otp(req: ResendOTPRequest, db: Session = Depends(get_db)):
    """
    Resend the login OTP to the user's email.
    Does NOT require a Bearer token — identified by email only.
    Validates that an active login OTP session exists before resending.
    """
    clean_email = req.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if not user:
        # Don't leak whether account exists
        return {"message": "If the session is active, a new code has been sent.", "dev_mode": False, "delivered": False}

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is inactive.")

    if is_user_locked(db, user.id, OTPPurpose.LOGIN):
        raise HTTPException(
            status_code=429,
            detail="Account is temporarily locked due to too many failed attempts. Please try again in 15 minutes."
        )

    otp_code = db.query(OtpCode).filter(
        OtpCode.user_id == user.id,
        OtpCode.purpose == OTPPurpose.LOGIN,
        OtpCode.used == False
    ).order_by(OtpCode.created_at.desc()).first()

    if not otp_code:
        raise HTTPException(
            status_code=400,
            detail="No active verification session found. Please sign in again."
        )

    if otp_code.resend_count >= 3:
        raise HTTPException(
            status_code=429,
            detail="Maximum resend attempts reached. Please sign in again to request a new code."
        )

    new_otp = generate_otp()
    otp_code.hashed_otp = get_password_hash(new_otp)
    otp_code.expires_at = datetime.utcnow() + timedelta(minutes=5)
    otp_code.resend_count += 1
    db.commit()

    delivery_res = EmailService.send_login_otp(user.email, new_otp)
    return {
        "message": "Verification code resent successfully.",
        "dev_mode": delivery_res.get("dev_mode", False),
        "delivered": delivery_res.get("delivered", False),
        "dev_note": delivery_res.get("message") if delivery_res.get("dev_mode") else None
    }


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    clean_email = req.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if not user:
        # Don't leak user existence
        dev_mode = not bool(settings.SMTP_HOST and settings.SMTP_HOST.strip())
        return {
            "message": "If the email is registered, a verification code has been sent.",
            "dev_mode": dev_mode,
            "delivered": not dev_mode
        }

    if is_user_locked(db, user.id, OTPPurpose.RESET_PASSWORD):
        raise HTTPException(status_code=429, detail="Account is temporarily locked due to too many failed OTP attempts. Try again in 15 minutes.")

    db.query(OtpCode).filter(OtpCode.user_id == user.id, OtpCode.purpose == OTPPurpose.RESET_PASSWORD, OtpCode.used == False).update({"used": True})
    
    otp = generate_otp()
    otp_code = OtpCode(
        user_id=user.id,
        purpose=OTPPurpose.RESET_PASSWORD,
        hashed_otp=get_password_hash(otp),
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(otp_code)
    db.commit()

    delivery_res = EmailService.send_password_reset_otp(user.email, otp)
    return {
        "message": delivery_res.get("message", "If the email is registered, a verification code has been sent."),
        "dev_mode": delivery_res.get("dev_mode", False),
        "delivered": delivery_res.get("delivered", False),
        "dev_note": delivery_res.get("message") if delivery_res.get("dev_mode") else None
    }


@router.post("/verify-reset-otp")
def verify_reset_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    clean_email = req.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid request")

    otp_code = db.query(OtpCode).filter(
        OtpCode.user_id == user.id,
        OtpCode.purpose == OTPPurpose.RESET_PASSWORD,
        OtpCode.used == False
    ).order_by(OtpCode.created_at.desc()).first()

    if not otp_code or otp_code.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired or invalid")

    if not verify_password(req.otp, otp_code.hashed_otp):
        lock_user(db, otp_code)
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    # DO NOT MARK USED YET! It will be used in /reset-password
    return {"message": "OTP verified successfully"}


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    clean_email = req.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid request")

    if is_user_locked(db, user.id, OTPPurpose.RESET_PASSWORD):
        raise HTTPException(status_code=429, detail="Account is locked.")

    otp_code = db.query(OtpCode).filter(
        OtpCode.user_id == user.id,
        OtpCode.purpose == OTPPurpose.RESET_PASSWORD,
        OtpCode.used == False
    ).order_by(OtpCode.created_at.desc()).first()

    if not otp_code or otp_code.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired or invalid")

    if not verify_password(req.otp, otp_code.hashed_otp):
        lock_user(db, otp_code)
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    user.hashed_password = get_password_hash(req.new_password)
    otp_code.used = True
    db.commit()


    return {"message": "Password reset successful"}


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
