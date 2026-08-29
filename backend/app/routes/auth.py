"""
Minimal auth endpoint (demo).

Production should swap this for OAuth2/JWT with proper password hashing.
A fixed demo credential set is used so the frontend can exercise the flow.
"""
import hmac
import os
import time

from fastapi import APIRouter, HTTPException

from backend.app.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api", tags=["auth"])

DEMO_USER = os.environ.get("DEMO_USER", "admin")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "admin123")


def _fake_jwt(username: str) -> str:
    """Deterministic demo token (HMAC-signed payload, not a real JWT)."""
    payload = f"{username}.{int(time.time() // 3600)}"
    signature = hmac.new(b"invoice-demo-secret", payload.encode(), "sha256").hexdigest()[:32]
    return f"{payload}.{signature}"


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    if not (hmac.compare_digest(body.username, DEMO_USER)
            and hmac.compare_digest(body.password, DEMO_PASSWORD)):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return TokenResponse(access_token=_fake_jwt(body.username))