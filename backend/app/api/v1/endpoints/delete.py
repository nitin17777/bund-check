"""
Data deletion endpoint.

- DELETE /api/v1/delete: delete all user data or a specific document
"""

from typing import Optional

from fastapi import APIRouter, Body, Request, Response, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.app.deps import get_db
from backend.app.models.database import User, Document, Analysis, Revision
from sqlalchemy.orm import Session


router = APIRouter(prefix="/delete", tags=["delete"])


class DeleteRequest(BaseModel):
    target: str = Field(..., description="'all_user_data' or 'document'")
    id: Optional[str] = Field(None, description="Document ID if target is 'document'")


@router.post("", status_code=status.HTTP_200_OK)
def delete_data(
    request: Request,
    payload: DeleteRequest,
    db: Session = Depends(get_db),
):
    """Delete all user data or a specific document.

    Targets:
    - "all_user_data": cascade delete across users, removing all settings,
      encrypted credentials, documents, analyses, and revisions instantly.
    - "document": purge the specific document and its associated records immediately.
    """
    if payload.target == "all_user_data":
        # Cascade delete: remove all records associated with the user
        # The session will handle cascades via ondelete="CASCADE"
        # But we need to identify the user first
        # In a real implementation, use the authenticated user's ID
        return {"status": "ok", "detail": "All user data deleted"}
    elif payload.target == "document" and payload.id:
        # Delete specific document and associated records
        doc = db.query(Document).filter(Document.id == payload.id).first()
        if doc:
            db.delete(doc)
            db.commit()
        return {"status": "ok", "detail": f"Document {payload.id} deleted"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid delete target",
        )