"""
FastAPI auth middleware for the MCP server.
Validates JWT before every request except health/docs.
"""

import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from mcp.shared.security import validate_token

logger = logging.getLogger(__name__)

SKIP_AUTH_PATHS = {"/health", "/docs", "/openapi.json", "/tools"}


async def mcp_auth_middleware(request: Request, call_next):
    if request.url.path in SKIP_AUTH_PATHS:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error":     "authentication_required",
                "message":   (
                    "Login at POST /api/v1/auth/login or via "
                    "Azure Entra ID, then include: "
                    "Authorization: Bearer <token>"
                ),
                "login_url": "/api/v1/auth/login",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(" ")[1]

    try:
        user_context = await validate_token(token)
        request.state.user_context = user_context
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "invalid_token", "message": str(e)},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await call_next(request)
