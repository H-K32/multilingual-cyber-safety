# backend/app/auth.py
"""Authentication and Role-Based Authorization for Bank Security Operations Feed.

Provides secure credential verification, role-based access control, and tenant
metadata derivation for financial institutions and security analysts querying Dagu
threat intelligence feeds.

Security Controls
-----------------
1. No hardcoded API keys or default credentials.
2. Configured strictly via environment variable `DAGU_SECURITY_FEED_API_KEYS`.
3. Safe fallback: If no keys are configured in the environment, all access to the
   feed is rejected with HTTP 401/503.
4. Timing-attack mitigation: Uses `hmac.compare_digest` for token comparisons.
5. Server-derived authorization: Client-supplied roles or organization names are
   ignored; the analyst's identity, role, and organization are bound strictly to
   the validated server-side token.
"""

from dataclasses import dataclass
import hmac
import json
import os
from typing import Dict, Optional

from fastapi import Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class SecurityAnalyst:
    """Authenticated security operations analyst or bank fraud investigator."""
    analyst_id: str
    organization: str
    role: str  # "analyst" | "admin" | "viewer"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def can_review(self) -> bool:
        return self.role in ("analyst", "admin")


def _load_authorized_keys() -> Dict[str, SecurityAnalyst]:
    """Parse authorized keys and role metadata from the environment.

    Supports:
    1. JSON map in DAGU_SECURITY_FEED_API_KEYS:
       {"secret-token-1": {"analyst_id": "cbe-01", "organization": "CBE", "role": "analyst"}}
    2. Comma-separated token strings:
       "token1:CBE:analyst:cbe-01,token2:Awash:analyst:awash-01"
    """
    raw = os.environ.get("DAGU_SECURITY_FEED_API_KEYS", "").strip()
    if not raw:
        return {}

    keys_map: Dict[str, SecurityAnalyst] = {}
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            for token, meta in data.items():
                if isinstance(meta, dict) and token:
                    keys_map[token] = SecurityAnalyst(
                        analyst_id=str(meta.get("analyst_id") or "analyst"),
                        organization=str(meta.get("organization") or "Partner Bank"),
                        role=str(meta.get("role") or "analyst").lower(),
                    )
            return keys_map
        except Exception:
            pass

    # Fallback comma-separated format: token:org:role:analyst_id
    for item in raw.split(","):
        parts = [p.strip() for p in item.split(":")]
        if len(parts) >= 3 and parts[0]:
            token = parts[0]
            org = parts[1]
            role = parts[2].lower()
            aid = parts[3] if len(parts) > 3 else f"{org.lower()}-analyst"
            keys_map[token] = SecurityAnalyst(
                analyst_id=aid,
                organization=org,
                role=role,
            )

    return keys_map


def get_current_security_analyst(
    bearer: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> SecurityAnalyst:
    """FastAPI dependency to authenticate bank security operations analysts.

    Checks `Authorization: Bearer <token>` and `X-API-Key: <token>`.
    Raises HTTP 401 if credentials are missing or invalid.
    Raises HTTP 503 if the server has not configured any feed credentials.
    """
    authorized_keys = _load_authorized_keys()
    if not authorized_keys:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Security operations feed authentication is not configured on this server. "
                "Contact the system administrator to provision API access."
            ),
        )

    provided_token: Optional[str] = None
    if bearer and bearer.credentials:
        provided_token = bearer.credentials.strip()
    elif x_api_key:
        provided_token = x_api_key.strip()

    if not provided_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing security operations authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Constant-time token lookup
    matched_analyst: Optional[SecurityAnalyst] = None
    for token, analyst in authorized_keys.items():
        if hmac.compare_digest(token, provided_token):
            matched_analyst = analyst
            break

    if matched_analyst is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired security operations credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return matched_analyst


def require_analyst_role(
    analyst: SecurityAnalyst = Security(get_current_security_analyst),
) -> SecurityAnalyst:
    """Dependency verifying analyst or admin permissions."""
    if not analyst.can_review:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Analyst or Admin role required.",
        )
    return analyst


def require_admin_role(
    analyst: SecurityAnalyst = Security(get_current_security_analyst),
) -> SecurityAnalyst:
    """Dependency verifying administrative permissions."""
    if not analyst.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Security Administrator role required.",
        )
    return analyst

