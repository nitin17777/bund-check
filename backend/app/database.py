"""
Database session management.

Creates the SQLAlchemy engine and session local class
used across the FastAPI application.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL if hasattr(settings, "DATABASE_URL") else "sqlite:///./test.db",
    echo=False,
    future=True,
)

# Create session local class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)