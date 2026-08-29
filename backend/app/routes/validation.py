"""Invoice validation endpoints (Phase 4: rule-based validation engine).

POST /api/validate/{batch_id} — run the rule-based validation engine over
every stored invoice of an upload batch, persist findings + updated status
into the DB and return a batch validation summary.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import BatchValidationSummary
from backend.app.services.validation_service import (
    BatchNotFoundError,
    ValidationError,
    validate_batch,
)

router = APIRouter(prefix="/api/validate", tags=["validation"])


@router.post("/{batch_id}", response_model=BatchValidationSummary)
def validate_batch_endpoint(batch_id: int, db: Session = Depends(get_db)):
    try:
        return validate_batch(db, batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=500, detail=str(exc))