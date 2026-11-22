from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.core.security import decode_token, is_token_revoked
from app.models.all_models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


_db_initialized = False


def ensure_db_initialized() -> int:
    """Ensure database schema is created and demo users are seeded. Returns user count."""
    global _db_initialized
    from app.database.session import Base, engine
    from app.database.seed import seed_database
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    init_db = SessionLocal()
    try:
        seed_database(init_db, fast_mode=True)
        count = init_db.query(User).count()
        _db_initialized = True
        return count
    except Exception:
        return 0
    finally:
        init_db.close()


def get_db() -> Generator:
    global _db_initialized
    if not _db_initialized:
        ensure_db_initialized()

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _resolve_user_from_payload(db: Session, payload: dict) -> Optional[User]:
    user_id = payload.get("sub")
    email = payload.get("email")

    user = None
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()

    if not user and email:
        user = db.query(User).filter(User.email == email.lower()).first()

    # If demo user in ephemeral container was cleared, re-seed and retry
    if not user and email in ("admin@talentmatch.ai", "recruiter@talentmatch.ai"):
        from app.database.seed import seed_database
        seed_database(db, fast_mode=True)
        user = db.query(User).filter(User.email == email.lower()).first()

    return user


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    """
    Strict authentication dependency.
    Raises 401 Unauthorized if token is missing, invalid, expired, or revoked.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required to access this resource",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = _resolve_user_from_payload(db, payload)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or deactivated"
        )
    return user


def get_optional_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    """Optional authentication dependency for mixed or public endpoints."""
    if not token or is_token_revoked(token):
        return None

    payload = decode_token(token)
    if not payload:
        return None

    user = _resolve_user_from_payload(db, payload)
    return user if user and user.is_active else None


def require_role(allowed_roles: list):
    """Enforce role-based access control (RBAC)."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if not current_user or current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the following roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


get_current_admin = require_role(["super_admin"])
get_current_recruiter_or_admin = require_role(["super_admin", "recruiter"])
