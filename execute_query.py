"""
execute_query (Server 2 tool, per MCP.md spec)

Executes a SQL or data query against a connected source.
Supports a source parameter, optional parameters, and row
limit handling. Main tool for operational data retrieval.

Depends on: connector registry
"""

import logging
from typing import Any

from connectors.registry import get_registry
from core.sql_validator import get_sql_validator

logger = logging.getLogger(__name__)


async def execute_query(
    arguments: dict[str, Any],
    user_context: dict[str, Any],
) -> dict[str, Any]:
    """
    arguments:
      source:     str  (required) — connector id
      query:      str  (required) — SQL to execute
      params:     dict (optional) — bind parameters
      row_limit:  int  (optional, default 1000)
      session_id: str  (optional)

    returns:
      success, rows, columns, row_count, execution_ms, error
    """
    source     = arguments.get("source", "").strip()
    query      = arguments.get("query", "").strip()
    row_limit  = int(arguments.get("row_limit", 1000))
    session_id = arguments.get("session_id", "")

    if not source:
        raise ValueError("source is required")
    if not query:
        raise ValueError("query is required")

    registry = get_registry()
    try:
        connector = registry.get(source)
    except KeyError:
        raise ValueError(
            f"Source '{source}' not found. Use list_sources "
            f"to see registered sources."
        )

    # Final safety validation before execution
    validator  = get_sql_validator()
    dialect    = connector.get_dialect()
    validation = validator.validate(sql=query, dialect=dialect)
    if not validation.valid:
        raise ValueError(
            f"Query rejected: {validation.reason}. "
            f"{validation.suggestion}"
        )

    result = await connector.execute(sql=query)

    logger.info(
        "mcp.execute_query | Complete",
        extra={
            "source":       source,
            "row_count":    result.row_count,
            "execution_ms": result.execution_ms,
            "success":      result.succeeded,
        },
    )

    return {
        "success":      result.succeeded,
        "rows":         result.rows[:row_limit],
        "columns":      result.columns,
        "row_count":    result.row_count,
        "execution_ms": result.execution_ms,
        "truncated":    result.truncated,
        "error":        result.error,
        "source":       source,
  }
