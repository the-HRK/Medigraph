"""
search_docs (Server 2 tool, per MCP.md spec)

Searches documents in a connected source such as SharePoint,
S3, or similar document repositories. Semantic document
search rather than direct SQL access.

Depends on: connector registry
"""

import logging
from typing import Any

from connectors.registry import get_registry

logger = logging.getLogger(__name__)


async def search_docs(
    arguments: dict[str, Any],
    user_context: dict[str, Any],
) -> dict[str, Any]:
    """
    arguments:
      source: str (required) — connector id (e.g. sharepoint)
      query:  str (required)
      limit:  int (optional, default 5)

    returns:
      results: list[dict] — document name, snippet, score
      total: int
    """
    source = arguments.get("source", "").strip()
    query  = arguments.get("query", "").strip()
    limit  = int(arguments.get("limit", 5))

    if not source:
        raise ValueError("source is required")
    if not query:
        raise ValueError("query is required")

    registry = get_registry()
    try:
        connector = registry.get(source)
    except KeyError:
        raise ValueError(f"Source '{source}' not found.")

    if not hasattr(connector, "search_documents"):
        raise ValueError(
            f"Source '{source}' does not support document search."
        )

    results = await connector.search_documents(query=query, limit=limit)

    logger.info(
        "mcp.search_docs | Complete",
        extra={"source": source, "results": len(results)},
    )

    return {
        "results": [
            {
                "document_name": r.document_name,
                "snippet":       r.snippet,
                "score":         round(r.score, 4),
                "path":          r.path,
            }
            for r in results
        ],
        "total":  len(results),
        "source": source,
  }
