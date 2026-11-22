from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, oauth2_scheme
from app.core.config import settings
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token,
    is_token_revoked,
    create_password_reset_token,
    verify_password_reset_token
)
from app.models.all_models import User
from app.schemas.all_schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserResponse,
    UserUpdate
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
@router.post("/register/", response_model=TokenResponse, include_in_schema=False)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    user = User(
        email=req.email.lower(),
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
        role=req.role or "recruiter",
        is_active=True,
        last_login=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user.id, role=user.role, email=user.email)
    refresh_token = create_refresh_token(user.id)

    NotificationService.log_activity(
        db=db,
        action="USER_REGISTER",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        details={"email": user.email}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login", response_model=TokenResponse)
@router.post("/login/", response_model=TokenResponse, include_in_schema=False)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email_clean = req.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    
    # If demo account is requested but not in DB yet, seed and retry
    if not user and email_clean in ("admin@talentmatch.ai", "recruiter@talentmatch.ai"):
        from app.database.seed import seed_database
        seed_database(db, fast_mode=True)
        user = db.query(User).filter(User.email == email_clean).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(user.id, role=user.role, email=user.email)
    refresh_token = create_refresh_token(user.id)

    NotificationService.log_activity(
        db=db,
        action="USER_LOGIN",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        details={"email": user.email}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/logout")
def logout(
    token: Optional[str] = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if token:
        revoke_token(token)
    NotificationService.log_activity(
        db=db,
        action="USER_LOGOUT",
        entity_type="user",
        entity_id=current_user.id,
        user_id=current_user.id,
        details={"email": current_user.email}
    )
    return {"message": "Logged out successfully, session invalidated"}


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    req: Optional[RefreshTokenRequest] = None,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Refresh Token Rotation:
    Validates the refresh token, revokes the used token,
    and returns a newly issued access token and rotated refresh token.
    """
    raw_token = req.refresh_token if (req and req.refresh_token) else token
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required"
        )

    if is_token_revoked(raw_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked or already used"
        )

    payload = decode_token(raw_token)
    if not payload or payload.get("type") not in ["refresh", "access"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account inactive or not found"
        )

    # Invalidate old token to prevent reuse attacks
    revoke_token(raw_token)

    # Issue new pair (Rotation)
    new_access = create_access_token(user.id, role=user.role)
    new_refresh = create_refresh_token(user.id)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "user": user
    }


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Safe Password Reset Request:
    Generates a secure password reset token without disclosing whether the email exists.
    """
    user = db.query(User).filter(User.email == req.email.lower()).first()
    reset_token = None
    if user and user.is_active:
        reset_token = create_password_reset_token(user.email)
        NotificationService.log_activity(
            db=db,
            action="PASSWORD_RESET_REQUEST",
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            details={"email": user.email}
        )
    # Always return a uniform response to prevent user enumeration
    # Return reset_token only in DEBUG mode for development and test execution
    return {
        "message": "If this email is registered in TalentMatch AI, a password reset token has been generated.",
        "reset_token": reset_token if settings.DEBUG else None
    }


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset user password using verified reset token."""
    if is_token_revoked(req.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has already been used or revoked."
        )

    email = verify_password_reset_token(req.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or malformed password reset token."
        )

    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with this reset token no longer exists."
        )

    user.hashed_password = hash_password(req.new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Invalidate token to prevent reuse attacks
    revoke_token(req.token)

    NotificationService.log_activity(
        db=db,
        action="PASSWORD_RESET_SUCCESS",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        details={"email": user.email}
    )

    return {"message": "Password has been successfully updated. You may now log in."}


@router.get("/me", response_model=UserResponse)
@router.get("/me/", response_model=UserResponse, include_in_schema=False)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name
    if user_in.email is not None:
        new_email = user_in.email.lower()
        if new_email != current_user.email:
            existing = db.query(User).filter(User.email == new_email).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A user with this email address already exists."
                )
            current_user.email = new_email
    if user_in.password:
        if len(user_in.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long."
            )
        current_user.hashed_password = hash_password(user_in.password)

    db.commit()
    db.refresh(current_user)
    return current_user
