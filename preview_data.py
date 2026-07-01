"""
preview_data (Server 2 tool, per MCP.md spec)

Pulls sample rows from a table. Limits output to small
samples for inspection.

Depends on: connector registry
"""

import logging
from typing import Any

from connectors.registry import get_registry

logger = logging.getLogger(__name__)

MAX_PREVIEW_ROWS = 20


async def preview_data(
    arguments: dict[str, Any],
    user_context: dict[str, Any],
) -> dict[str, Any]:
    """
    arguments:
      source: str (required) — connector id
      table:  str (required) — full table name
      limit:  int (optional, default 5, capped at 20)

    returns:
      rows, columns, row_count
    """
    source = arguments.get("source", "").strip()
    table  = arguments.get("table", "").strip()
    limit  = min(int(arguments.get("limit", 5)), MAX_PREVIEW_ROWS)

    if not source:
        raise ValueError("source is required")
    if not table:
        raise ValueError("table is required")

    registry = get_registry()
    try:
        connector = registry.get(source)
    except KeyError:
        raise ValueError(f"Source '{source}' not found.")

    dialect = connector.get_dialect()
    sql     = f"SELECT * FROM {table} LIMIT {limit}"

    result = await connector.execute(sql=sql)

    logger.info(
        "mcp.preview_data | Complete",
        extra={"source": source, "table": table, "rows": result.row_count},
    )

    return {
        "source":    source,
        "table":     table,
        "rows":      result.rows,
        "columns":   result.columns,
        "row_count": result.row_count,
        "error":     result.error,
    }
  
