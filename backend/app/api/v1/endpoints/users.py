"""
User authentication endpoints.

- POST /api/v1/auth/register: create a new user account
- POST /api/v1/auth/login: login and set httpOnly session cookie
- POST /api/v1/auth/logout: clear session cookie
"""

from fastapi import APIRouter, Body, Request, Response, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.app.deps import password_hash, verify_password
from backend.app.models.database import User
from backend.app.database import SessionLocal, engine
from sqlalchemy.orm import Session


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Plain text password")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Plain text password")


def get_db():
    """Dependency that provides a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    request: Request,
    response: Response,
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new user account."""
    # Check if user already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    # Create user with argon2 hash
    hashed = password_hash(payload.password)
    user = User(email=payload.email, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Set httpOnly session cookie
    import uuid
    session_id = str(uuid.uuid4())
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path="/",
    )
    # Store session ID in user (simplified)
    user.session_id = session_id  # type: ignore
    db.commit()
    
    return {"status": "ok", "user_id": str(user.id)}


@router.post("/login", status_code=status.HTTP_200_OK)
def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """Login and set httpOnly session cookie."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # Set httpOnly session cookie
    import uuid
    session_id = str(uuid.uuid4())
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path="/",
    )
    # Update user's session ID
    user.session_id = session_id  # type: ignore
    db.commit()
    
    return {"status": "ok", "user_id": str(user.id)}


@router.post("/logout")
def logout(
    response: Response,
):
    """Clear the session cookie."""
    response.delete_cookie(
        key="session_id",
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )
    return {"status": "ok"}