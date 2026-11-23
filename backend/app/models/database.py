"""
SQLAlchemy 2.0 ORM models for BundCheck backend.

Tables:
- users: authentication and account data (opt-in only persistence)
- user_settings: user preferences & encrypted provider keys
- documents: opt-in uploaded document records (never stored by default)
- analyses: opt-in analysis results (scores/stats without document text when not opted in)
- revisions: opt-in revision history for writing improvements
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import uuid

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    JSON,
    ForeignKey,
    Index,
    LargeBinary,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 Declarative base."""


# ──────────────────────────────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────────────────────────────

class User(Base):
    """User account model with email/password auth.

    Auth: email + password (argon2) with httpOnly session cookies.
    No secrets in code — all credentials loaded from environment variables.
    """

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        UUID(36), primary_key=True, default=lambda: uuid.uuid.uuid4()
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    settings: Mapped["UserSettings"] = relationship(
        "UserSettings", back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="user", cascade="all, delete-orphan"
    )
    analyses: Mapped[List["Analysis"]] = relationship(
        "Analysis", back_populates="user", cascade="all, delete-orphan"
    )
    revisions: Mapped[List["Revision"]] = relationship(
        "Revision", back_populates="user", cascade="all, delete-orphan"
    )


# ──────────────────────────────────────────────────────────────────────
# User Settings
# ──────────────────────────────────────────────────────────────────────

class UserSettings(Base):
    """User preferences and encrypted provider keys.

    Persisted. Controls default store opt-in, improvement mode,
    sensitivity preference, and encrypted LLM provider keys.
    """

    __tablename__ = "user_settings"

    user_id: Mapped[UUID] = mapped_column(
        UUID(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    store_history_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    default_improver_mode: Mapped[str] = mapped_column(
        String(50), nullable=False, default="academic_clarity"
    )
    sensitivity_preference: Mapped[str] = mapped_column(
        String(30), nullable=False, default="balanced"
    )
    encrypted_groq_key: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary, nullable=True
    )
    encrypted_openrouter_key: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary, nullable=True
    )
    encrypted_anthropic_key: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary, nullable=True
    )
    encrypted_openai_key: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary, nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="settings")


# ──────────────────────────────────────────────────────────────────────
# Documents (opt-in only)
# ──────────────────────────────────────────────────────────────────────

class Document(Base):
    """Opt-in uploaded document record.

    Raw text is never stored on disk regardless of opt-in;
    only extracted text is saved if the user has opted in.
    """

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        UUID(36), primary_key=True, default=lambda: uuid.uuid4()
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # encrypted_raw_text: stored only when user opts in (app-layer encryption)
    encrypted_raw_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    retention_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
        + __import__("datetime").timedelta(days=30),
    )

    # Indexes for retention cleanup
    __table_args__ = (
        Index("idx_documents_retention", "retention_expires_at"),
        Index("idx_documents_user_id", "user_id"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="documents")
    analyses: Mapped[List["Analysis"]] = relationship(
        "Analysis", back_populates="document", cascade="all, delete-orphan"
    )
    revisions: Mapped[List["Revision"]] = relationship(
        "Revision", back_populates="document", cascade="all, delete-orphan"
    )


# ──────────────────────────────────────────────────────────────────────
# Analyses (opt-in only)
# ──────────────────────────────────────────────────────────────────────

class Analysis(Base):
    """Opt-in analysis result from the content checker.

    Stores scores and stats without document text when the user
    has not opted in. When opted in, stores anonymized signals and
    sentence attribution linked to a document.

    The raw input text is never stored to disk — processed in ephemeral
    memory and discarded immediately after response dispatch.
    """

    __tablename__ = "analyses"

    id: Mapped[UUID] = mapped_column(
        UUID(36), primary_key=True, default=lambda: uuid.uuid4()
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    synthetic_pattern_confidence: Mapped[float] = mapped_column(
        nullable=False
    )
    classification_band: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    uncertainty_lower: Mapped[float] = mapped_column(nullable=False)
    uncertainty_upper: Mapped[float] = mapped_column(nullable=False)
    signals: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    sentence_attribution: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    retention_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
        + __import__("datetime").timedelta(days=30),
    )

    # Indexes for retention cleanup
    __table_args__ = (
        Index("idx_analyses_user_id", "user_id"),
        Index("idx_analyses_retention", "retention_expires_at"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="analyses")
    document: Mapped[Optional["Document"]] = relationship(
        "Document", back_populates="analyses"
    )


# ──────────────────────────────────────────────────────────────────────
# Revisions (opt-in only)
# ──────────────────────────────────────────────────────────────────────

class Revision(Base):
    """Opt-in revision history record for writing improvements.

    Stores the mode, original text, rewritten text, diff data,
    and verification status. Only persisted when user opts in.
    """

    __tablename__ = "revisions"

    id: Mapped[UUID] = mapped_column(
        UUID(36), primary_key=True, default=lambda: uuid.uuid4()
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    rewritten_text: Mapped[str] = mapped_column(Text, nullable=False)
    diff_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    verification_report: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    retention_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
        + __import__("datetime").timedelta(days=30),
    )

    # Indexes for retention cleanup
    __table_args__ = (
        Index("idx_revisions_user_id", "user_id"),
        Index("idx_revisions_retention", "retention_expires_at"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="revisions")
    document: Mapped[Optional["Document"]] = relationship(
        "Document", back_populates="revisions"
    )