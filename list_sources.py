"""
list_sources (Server 2 tool, per MCP.md spec)

Lists all registered data sources and shows whether they
are enabled.

Depends on: connector registry
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from connectors.registry import get_registry
from models.connector import RegisteredConnector

logger = logging.getLogger(__name__)


async def list_sources(
    db: AsyncSession,
    arguments: dict[str, Any],
    user_context: dict[str, Any],
) -> dict[str, Any]:
    """
    arguments: none required

    returns:
      sources: list[dict] — id, name, type, enabled, status
      total: int
    """
    org_id = user_context.get("org_id", "")

    result = await db.execute(
        select(RegisteredConnector).where(
            RegisteredConnector.org_id == org_id
        )
    )
    rows = result.scalars().all()

    logger.info(
        "mcp.list_sources | Complete",
        extra={"org_id": org_id, "count": len(rows)},
    )

    return {
        "sources": [
            {
                "id":      str(r.id),
                "name":    r.name,
                "type":    r.connector_type,
                "enabled": r.is_active,
                "status":  r.status,
            }
            for r in rows
        ],
        "total": len(rows),
  }
