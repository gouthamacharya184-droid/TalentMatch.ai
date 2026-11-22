import base64
import hashlib
import hmac
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import settings

try:
    import bcrypt

    _HAS_BCRYPT = True
except Exception:
    _HAS_BCRYPT = False


def _hash_pbkdf2(password: str) -> str:
    """Pure-Python PBKDF2 fallback hashing for serverless environments."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"pbkdf2_sha256$100000${base64.b64encode(salt).decode('ascii')}${base64.b64encode(key).decode('ascii')}"


def _verify_pbkdf2(plain_password: str, hashed_password: str) -> bool:
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = base64.b64decode(parts[2].encode("ascii"))
        expected_key = base64.b64decode(parts[3].encode("ascii"))
        computed_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(expected_key, computed_key)
    except Exception:
        return False


def hash_password(password: str) -> str:
    """Hash password using bcrypt with PBKDF2 pure-Python fallback."""
    if _HAS_BCRYPT:
        try:
            password_bytes = password.encode("utf-8")[:72]
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password_bytes, salt)
            return hashed.decode("utf-8")
        except Exception:
            pass
    return _hash_pbkdf2(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt or pbkdf2 hash."""
    if not hashed_password or not plain_password:
        return False
    if hashed_password.startswith("pbkdf2_sha256$"):
        return _verify_pbkdf2(plain_password, hashed_password)
    if _HAS_BCRYPT:
        try:
            plain_bytes = plain_password.encode("utf-8")[:72]
            hash_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(plain_bytes, hash_bytes)
        except Exception:
            return False
    return False


def create_access_token(
    subject: str | Any, role: str = "recruiter", email: str | None = None, expires_delta: timedelta | None = None
) -> str:
    """Create JWT access token with role and optional email claim."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": datetime.now(UTC),
        "jti": str(uuid.uuid4()),
        "type": "access",
    }
    if email:
        to_encode["email"] = str(email).lower()
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str | Any) -> str:
    """Create JWT refresh token."""
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(UTC),
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except Exception:
        return None


# In-memory revocation cache for instant lookups
_REVOKED_TOKENS = set()


def revoke_token(token: str, db=None, reason: str = "logout") -> None:
    """Add a token to in-memory cache and persistent database blocklist."""
    if not token:
        return
    _REVOKED_TOKENS.add(token)
    if db:
        try:
            from app.models.all_models import RevokedToken, generate_uuid, utc_now

            payload = decode_token(token)
            exp_dt = None
            if payload and "exp" in payload:
                try:
                    exp_dt = datetime.fromtimestamp(payload["exp"], tz=UTC)
                except Exception:
                    pass

            existing = db.query(RevokedToken).filter(RevokedToken.token == token).first()
            if not existing:
                db.add(
                    RevokedToken(
                        id=generate_uuid(), token=token, reason=reason, created_at=utc_now(), expires_at=exp_dt
                    )
                )
                db.commit()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass


def is_token_revoked(token: str, db=None) -> bool:
    """Check if token has been invalidated by logout, refresh rotation, or revocation."""
    if not token:
        return False
    if token in _REVOKED_TOKENS:
        return True
    if db:
        try:
            from app.models.all_models import RevokedToken

            found = db.query(RevokedToken).filter(RevokedToken.token == token).first()
            if found:
                _REVOKED_TOKENS.add(token)
                return True
        except Exception:
            pass
    return False


def create_password_reset_token(email: str) -> str:
    """Create short-lived JWT token (15 mins) with unique JTI for replay-safe password reset."""
    expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode = {
        "sub": email.lower(),
        "exp": expire,
        "iat": datetime.now(UTC),
        "jti": str(uuid.uuid4()),
        "type": "password_reset",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_password_reset_token(token: str) -> str | None:
    """Verify password reset token and return user email if valid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except Exception:
        return None
