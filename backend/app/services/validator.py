"""Rule-based validator (Phase 4: rule-based validation engine).

Responsibility: run every rule from rules.py against ONE invoice and reduce
the findings into a deterministic risk score + invoice status.

Scoring (deterministic, no ML):
    CRITICAL  40
    ERROR     20
    WARNING   10
    INFO       2
Scores of all issues are summed and capped at 100.

Status (from invoices.risk_score):
    0       -> Valid
    1-29    -> Needs Review
    30-59   -> High Risk
    60-100  -> Critical
"""

from datetime import date

from backend.app.services.rules import (
    ALL_RULES,
    CRITICAL,
    ERROR,
    INFO,
    Issue,
    RuleContext,
    WARNING,
)

# Severity -> risk points (see phase brief).
SEVERITY_SCORES = {
    INFO: 2,
    WARNING: 10,
    ERROR: 20,
    CRITICAL: 40,
}

MAX_RISK_SCORE = 100.0


def calculate_risk_score(issues: list[Issue]) -> float:
    """Sum the severity-weighted points of all issues, capped at 100."""
    score = sum(SEVERITY_SCORES.get(issue.severity, 0) for issue in issues)
    return round(min(score, MAX_RISK_SCORE), 2)


def status_for_score(score: float) -> str:
    """Map a risk score (0-100) to the invoice status per the phase brief."""
    if score <= 0:
        return "Valid"
    if score <= 29:
        return "Needs Review"
    if score <= 59:
        return "High Risk"
    return "Critical"


def run_all_rules(invoice, items, *, today=None, total_tolerance: float = 0.01) -> list[Issue]:
    """Run the full rule set against one invoice + its line items."""
    if today is None:
        today = date.today()
    context = RuleContext(today=today, total_tolerance=total_tolerance)
    issues: list[Issue] = []
    for rule in ALL_RULES:
        issues.extend(rule(invoice, items, context))
    return issues


def assess(invoice, items, *, today=None, total_tolerance: float = 0.01) -> dict:
    """Validate one invoice: returns {"issues", "risk_score", "status"}."""
    issues = run_all_rules(invoice, items, today=today, total_tolerance=total_tolerance)
    risk_score = calculate_risk_score(issues)
    return {
        "issues": issues,
        "risk_score": risk_score,
        "status": status_for_score(risk_score),
        "has_critical": any(issue.severity == CRITICAL for issue in issues),
    }