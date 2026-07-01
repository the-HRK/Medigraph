"""
Shared security layer for the MCP server.
Handles authentication, authorization (RBAC), and rate limiting.

Supports two token issuers:
1. Internal auth (our own JWT)
2. Azure Entra ID (Teams, Copilot Studio, enterprise SSO)
"""

import logging
import time
from typing import Any

import httpx
import redis.asyncio as aioredis
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from config import get_settings
from database import AsyncSessionLocal
from auth_service import get_auth_service

logger   = logging.getLogger(__name__)
settings = get_settings()

_jwks_cache: dict | None = None
_redis: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url, decode_responses=True
        )
    return _redis


# ── Authentication ────────────────────────────────────────────

async def validate_token(token: str) -> dict[str, Any]:
    """
    Validates JWT and returns user context.
    Routes to Azure Entra ID or internal validation
    based on token issuer.

    Returns:
    {
        "user_id": str,
        "email":   str,
        "org_id":  str,
        "roles":   list[str],
        "source":  "azure_entra" | "internal"
    }
    """
    if not token:
        raise ValueError(
            "No token provided. Login at POST /api/v1/auth/login "
            "or authenticate via Azure Entra ID, then include "
            "the token as: Authorization: Bearer <token>"
        )

    try:
        unverified = jwt.get_unverified_claims(token)
        issuer = unverified.get("iss", "")
    except Exception:
        raise ValueError("Token is malformed.")

    if settings.AZURE_TENANT_ID and "microsoftonline" in issuer:
        return await _validate_azure_token(token)
    return await _validate_internal_token(token)


async def _get_azure_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache
    url = (
        f"https://login.microsoftonline.com/"
        f"{settings.AZURE_TENANT_ID}/discovery/v2.0/keys"
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        _jwks_cache = response.json()
    return _jwks_cache


async def _validate_azure_token(token: str) -> dict[str, Any]:
    try:
        jwks = await _get_azure_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.AZURE_CLIENT_ID,
            issuer=(
                f"https://login.microsoftonline.com/"
                f"{settings.AZURE_TENANT_ID}/v2.0"
            ),
            options={"verify_at_hash": False},
        )
        return {
            "user_id": payload.get("oid"),
            "email":   payload.get("preferred_username", ""),
            "org_id":  payload.get("tid"),
            "roles":   payload.get("roles", []),
            "source":  "azure_entra",
        }
    except ExpiredSignatureError:
        raise ValueError("Azure token expired. Re-authenticate.")
    except JWTError as e:
        raise ValueError(f"Azure token invalid: {e}")


async def _validate_internal_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            raise ValueError("Use access_token, not refresh_token.")

        user_id = payload.get("sub")
        auth = get_auth_service()
        async with AsyncSessionLocal() as db:
            user = await auth.get_user_by_id(db, user_id)

        if not user or not user.is_active:
            raise ValueError("User not found or inactive.")

        return {
            "user_id": str(user.id),
            "email":   user.email,
            "org_id":  str(user.org_id),
            "roles":   [user.role],
            "source":  "internal",
        }
    except ExpiredSignatureError:
        raise ValueError(
            "Token expired. POST /api/v1/auth/refresh"
        )
    except JWTError as e:
        raise ValueError(f"Token invalid: {e}")


# ── Authorization (RBAC) ──────────────────────────────────────

# Tools any authenticated user can call
PUBLIC_TOOLS = {
    "get_context",
    "search_knowledge_graph",
    "list_sources",
    "test_connection",
    "get_schema",
}

# Tools requiring analyst role or above
ANALYST_TOOLS = {
    "get_md_files",
    "execute_query",
    "search_docs",
    "preview_data",
}

ANALYST_ROLES = {"analyst", "admin", "superadmin"}


def check_tool_permission(
    user_context: dict[str, Any],
    tool_name: str,
) -> None:
    """
    RBAC check. Raises ValueError if user cannot call this tool.
    Fails closed — unknown tools are denied by default.
    """
    roles = set(user_context.get("roles", []))

    if tool_name in PUBLIC_TOOLS:
        return

    if tool_name in ANALYST_TOOLS:
        if not (roles & ANALYST_ROLES):
            raise ValueError(
                f"'{tool_name}' requires analyst role or above. "
                f"Your roles: {list(roles)}"
            )
        return

    raise ValueError(f"Unknown or unauthorized tool: {tool_name}")


# ── Rate Limiting ─────────────────────────────────────────────

RATE_LIMITS = {
    "get_md_files":           30,
    "search_knowledge_graph": 60,
    "get_context":            120,
    "execute_query":          10,
    "search_docs":            20,
    "get_schema":             30,
    "preview_data":           20,
    "list_sources":           60,
    "test_connection":        10,
}
DEFAULT_LIMIT = 60


async def check_rate_limit(user_id: str, tool_name: str) -> None:
    """Sliding window rate limit per user per tool per minute."""
    limit  = RATE_LIMITS.get(tool_name, DEFAULT_LIMIT)
    window = 60
    now    = int(time.time())
    key    = f"mcp:rate:{user_id}:{tool_name}:{now // window}"

    redis = _get_redis()
    pipe  = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, window * 2)
    count = (await pipe.execute())[0]

    if count > limit:
        retry_after = window - (now % window)
        raise ValueError(
            f"Rate limit exceeded for '{tool_name}'. "
            f"Limit: {limit}/min. Retry in {retry_after}s."
        )
