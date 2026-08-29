"""Backend service entry points (Phase 4 + Phase 5 API surface).

Imports are kept explicit so nothing from the legacy pandas / ML prototype
pipeline loads at import time. The rule-based validation engine is split
across rules/validator/validation_service; duplicate detection intelligence
across duplicate_rules/duplicate_matcher/duplicate_service.
"""
from backend.app.services.rules import ALL_RULES, Issue
from backend.app.services.validator import (
    calculate_risk_score,
    run_all_rules,
    status_for_score,
)
from backend.app.services.validation_service import (
    BatchNotFoundError,
    ValidationError,
    validate_batch,
)
from backend.app.services.duplicate_rules import (
    DUPLICATE_CODES,
    DUPLICATE_EXACT,
    DUPLICATE_VENDOR,
    DUPLICATE_NEAR,
    DUPLICATE_DATE,
    DUPLICATE_ITEM,
)
from backend.app.services.duplicate_service import (
    DuplicateScanError,
    list_duplicate_pairs,
    scan_duplicates,
)

__all__ = [
    "ALL_RULES",
    "Issue",
    "calculate_risk_score",
    "run_all_rules",
    "status_for_score",
    "BatchNotFoundError",
    "ValidationError",
    "validate_batch",
    "DUPLICATE_CODES",
    "DUPLICATE_EXACT",
    "DUPLICATE_VENDOR",
    "DUPLICATE_NEAR",
    "DUPLICATE_DATE",
    "DUPLICATE_ITEM",
    "DuplicateScanError",
    "list_duplicate_pairs",
    "scan_duplicates",
]