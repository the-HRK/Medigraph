"""
get_schema (Server 2 tool, per MCP.md spec)

Retrieves the schema for a source or topic. Helps understand
what tables or structures exist before querying.

Depends on: connector registry
"""

import logging
from typing import Any

from connectors.registry import get_registry

logger = logging.getLogger(__name__)


async def get_schema(
    arguments: dict[str, Any],
    user_context: dict[str, Any],
) -> dict[str, Any]:
    """
    arguments:
      source: str (required) — connector id
      topic:  str (optional) — narrows to a specific table/topic

    returns:
      tables: list[dict] — full_name, columns, dialect
    """
    source = arguments.get("source", "").strip()
    topic  = arguments.get("topic", "").strip()

    if not source:
        raise ValueError("source is required")

    registry = get_registry()
    try:
        connector = registry.get(source)
    except KeyError:
        raise ValueError(f"Source '{source}' not found.")

    dialect = connector.get_dialect()

    if topic:
        table = await connector.get_table_schema(topic)
        tables = [table] if table else []
    else:
        tables = await connector.list_schemas()

    logger.info(
        "mcp.get_schema | Complete",
        extra={"source": source, "tables": len(tables)},
    )

    return {
        "source":  source,
        "dialect": dialect.value,
        "tables": [
            {
                "full_name": t.full_name,
                "columns":   t.column_names,
            }
            for t in tables
        ],
        "total": len(tables),
  }
