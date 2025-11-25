"""
Security utilities for JWT authentication and password hashing.
"""
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import bcrypt
from jose import JWTError, jwt
from app.core.config import settings


def _pre_hash_password(password: str) -> bytes:
    """
    Pre-hash password with SHA256 to support passwords longer than 72 bytes.
    Returns bytes (32 bytes) which is well under bcrypt's 72-byte limit.
    This is a common workaround for bcrypt's 72-byte limit.
    """
    # SHA256 produces 32 bytes, which is safely under bcrypt's 72-byte limit
    return hashlib.sha256(password.encode('utf-8')).digest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    # Pre-hash the plain password to match the stored hash
    pre_hashed = _pre_hash_password(plain_password)
    # hashed_password is a string starting with $2b$, convert to bytes for bcrypt
    return bcrypt.checkpw(pre_hashed, hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    Pre-hashes with SHA256 first to support passwords longer than 72 bytes.
    Uses bcrypt directly to avoid passlib's backend detection issues.
    """
    # Pre-hash with SHA256 to support longer passwords
    # SHA256 digest is 32 bytes, which is safely under bcrypt's 72-byte limit
    pre_hashed = _pre_hash_password(password)
    # Generate salt and hash using bcrypt directly
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pre_hashed, salt)
    # Return as string for database storage
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

