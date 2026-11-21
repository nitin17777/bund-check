"""
Standardized Error Responses adhering to API_SPEC.md (RFC 7807 problem details).
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: List[ErrorDetail] = Field(default_factory=list)
    request_id: Optional[str] = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class DocumentProcessingException(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Optional[List[ErrorDetail]] = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []
        super().__init__(message)
