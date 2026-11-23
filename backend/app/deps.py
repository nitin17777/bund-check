"""
Dependency helpers for FastAPI endpoints.

Provides:
- get_current_user: retrieves the authenticated user from session cookie
- password_hash / verify_password: argon2 password helpers
- get_db_session: SQLAlchemy session dependency
"""

from typing import Generator, Optional

import argon2
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import get_limiter, rate_limit_exceeded_handler
from backend.app.database import SessionLocal, engine
from backend.app.models.database import User


password_hasher = argon2.PasswordHasher()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against an argon2 hash."""
    try:
        password_hasher.verify(hashed_password, plain_password)
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False
    except Exception:
        return False


def password_hash(plain_password: str) -> str:
    """Hash a plain password using argon2."""
    return password_hasher.hash(plain_password)


def get_db_session():
    """Dependency that provides a SQLAlchemy session."""
    from backend.app.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    db_session: Session = Depends(get_db_session),
) -> User:
    """Retrieve the authenticated user from the session cookie.

    Auth scheme: email + password with argon2 and httpOnly session cookies.
    The user's ID is stored in a signed session cookie; no secrets in code.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    # Look up user by session ID
    user = db_session.query(User).filter(User.id == session_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user