"""
test_connection (Server 2 tool, per MCP.md spec)

Verifies connectivity to a specific source.

Depends on: connector registry
"""

import logging
from typing import Any

from connectors.registry import get_registry

logger = logging.getLogger(__name__)


async def test_connection(
    arguments: dict[str, Any],
    user_context: dict[str, Any],
) -> dict[str, Any]:
    """
    arguments:
      source: str (required) — connector id

    returns:
      status, latency_ms, error
    """
    source = arguments.get("source", "").strip()
    if not source:
        raise ValueError("source is required")

    registry = get_registry()
    try:
        connector = registry.get(source)
    except KeyError:
        raise ValueError(f"Source '{source}' not found.")

    health = await connector.test_connection()

    logger.info(
        "mcp.test_connection | Complete",
        extra={"source": source, "status": health.status.value},
    )

    return {
        "source":     source,
        "status":     health.status.value,
        "latency_ms": health.latency_ms,
        "error":      health.error,
    }
