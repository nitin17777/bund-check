"""
Verification Service Package.

Exposes the multi-stage post-rewrite verification layer.
"""

from backend.app.services.verification.numbers import audit_numeric_integrity
from backend.app.services.verification.citations import audit_citation_integrity
from backend.app.services.verification.entities import audit_entity_integrity
from backend.app.services.verification.structure import audit_structure_integrity
from backend.app.services.verification.semantic import audit_semantic_integrity
from backend.app.services.verification.aggregate import run_full_verification

__all__ = [
    "audit_numeric_integrity",
    "audit_citation_integrity",
    "audit_entity_integrity",
    "audit_structure_integrity",
    "audit_semantic_integrity",
    "run_full_verification",
]
