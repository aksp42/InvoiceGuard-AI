from typing import List, Optional
from pydantic import BaseModel


class ValidationIssue(BaseModel):
    code: str
    message: str


class InvoiceResult(BaseModel):
    invoice_id: str
    vendor_name: Optional[str] = None
    total_amount: Optional[float] = None
    expected_total: Optional[float] = None
    status: str  # Valid / Needs Review / High Risk / Duplicate
    risk_score: float
    issues: List[ValidationIssue] = []


class ValidationSummary(BaseModel):
    total_invoices: int
    valid_count: int
    high_risk_count: int
    duplicate_count: int
    total_flagged_amount: float
    results: List[InvoiceResult]


class UploadSummary(BaseModel):
    batch_id: int
    file_name: str
    total: int
    processed: int
    failed: int
    status: str


class UploadHistoryItem(BaseModel):
    batch_id: int
    file_name: str
    uploaded_by: str
    uploaded_at: Optional[str]
    total_invoices: int
    processed_invoices: int
    failed_invoices: int
    status: str


class BatchInvoice(BaseModel):
    invoice_number: str
    invoice_date: Optional[str]
    vendor_name: Optional[str]
    subtotal: Optional[float]
    tax_amount: Optional[float]
    total_amount: Optional[float]
    status: str


class BatchDetail(BaseModel):
    batch_id: int
    file_name: str
    uploaded_by: str
    uploaded_at: Optional[str]
    total_invoices: int
    processed_invoices: int
    failed_invoices: int
    status: str
    invoices: List[BatchInvoice]


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BatchValidationSummary(BaseModel):
    batch_id: int
    total_invoices: int
    valid: int
    needs_review: int
    high_risk: int
    critical: int
    validation_time: str


class DuplicateSummary(BaseModel):
    batch_id: int
    exact_duplicates: int
    vendor_duplicates: int
    near_duplicates: int
    suspicious_duplicates: int


class DuplicateFindingPair(BaseModel):
    invoice_a_id: int
    invoice_a_number: Optional[str]
    invoice_b_id: int
    invoice_b_number: Optional[str]
    vendor_name: Optional[str]
    amount_a: Optional[float]
    amount_b: Optional[float]
    invoice_date_a: Optional[str]
    invoice_date_b: Optional[str]
    matched_ids: List[int]
    validation_type: str
    severity: str
    confidence_score: Optional[float]
    similarity: Optional[float]