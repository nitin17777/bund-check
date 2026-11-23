"""
Audit history endpoints.

- GET /api/v1/history: list user's analysis and revision records
"""

from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.app.deps import get_db
from backend.app.models.database import User, Analysis, Revision
from sqlalchemy.orm import Session
from sqlalchemy import select


router = APIRouter(prefix="/history", tags=["history"])


class AuditRecord(BaseModel):
    id: str = Field(description="analysis_id or revision_id")
    type: str = Field(description="check or improver")
    title: str = Field(description="Brief title")
    summary: str = Field(description="Short summary")
    word_count: int = Field(description="Word count")
    label_or_mode: str = Field(description="Detection label or improvement mode")
    timestamp: str = Field(description="ISO timestamp")
    document_filename: Optional[str] = Field(None, description="Associated document filename")


class HistoryListResponse(BaseModel):
    records: list[AuditRecord]
    count: int


@router.get("", response_model=HistoryListResponse, status_code=status.HTTP_200_OK)
def list_history(
    request: Request,
    db: Session = Depends(get_db),
):
    """List user's audit history records."""
    # In a real implementation, we'd filter by the authenticated user
    # For now, return empty list
    return {"records": [], "count": 0}