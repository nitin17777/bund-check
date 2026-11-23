"""
User settings endpoints.

- GET /api/v1/settings: retrieve user settings
- PUT /api/v1/settings: update user settings
"""

from typing import Optional

from fastapi import APIRouter, Body, Request, Response, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.app.deps import get_db
from backend.app.models.database import User, UserSettings
from sqlalchemy.orm import Session


router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsGetResponse(BaseModel):
    store_history_default: bool = Field(default=False, description="Whether to store documents by default")
    default_improver_mode: str = Field(default="academic_clarity", description="Default writing improvement mode")
    sensitivity_preference: str = Field(default="balanced", description="Sensitivity preference")
    data_retention_days: int = Field(default=30, description="Retention window in days")


class SettingsUpdateRequest(BaseModel):
    store_history_default: Optional[bool] = Field(None, description="Whether to store documents by default")
    default_improver_mode: Optional[str] = Field(None, description="Default writing improvement mode")
    sensitivity_preference: Optional[str] = Field(None, description="Sensitivity preference")
    data_retention_days: Optional[int] = Field(None, description="Retention window in days")


@router.get("", response_model=SettingsGetResponse, status_code=status.HTTP_200_OK)
def get_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # placeholder - will use session auth
):
    """Retrieve user settings."""
    # In a real implementation, we'd get the current user from the session
    # For now, return default settings
    return SettingsGetResponse()


@router.put("", status_code=status.HTTP_200_OK)
def update_settings(
    request: Request,
    payload: SettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None),  # placeholder
):
    """Update user settings."""
    # In a real implementation, we'd update the user's settings in the DB
    # For now, just return success
    return {"status": "ok"}