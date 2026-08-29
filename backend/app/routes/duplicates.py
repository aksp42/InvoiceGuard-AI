"""Duplicate detection endpoints (Phase 5: duplicate detection intelligence).

POST /api/duplicates/{batch_id}  — scan one upload batch for duplicate invoices
                                  and return the per-level summary counts
GET  /api/duplicates              — deduplicated duplicate-pair rows (flagged
                                  across all batches) for the Duplicates page
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import DuplicateFindingPair, DuplicateSummary
from backend.app.services import duplicate_service
from backend.app.services.validation_service import BatchNotFoundError

router = APIRouter(prefix="/api/duplicates", tags=["duplicates"])


@router.post("/{batch_id}", response_model=DuplicateSummary)
def scan_batch_duplicates(batch_id: int, db: Session = Depends(get_db)):
    """Detect duplicates for every invoice in the batch, persist + update risk."""
    try:
        return duplicate_service.scan_duplicates(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except duplicate_service.DuplicateScanError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("", response_model=list[DuplicateFindingPair])
def list_duplicates(db: Session = Depends(get_db)):
    """All detected duplicate pairs (deduplicated, one row per pair)."""
    try:
        return duplicate_service.list_duplicate_pairs(db)
    except Exception:  # pragma: no cover - infra dependent
        # Empty / unavailable database → empty list, not a 500.
        return []