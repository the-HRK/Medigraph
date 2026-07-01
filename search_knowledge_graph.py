"""
search_knowledge_graph (Server 1 tool, per MCP.md spec)

Searches knowledge graph nodes by term. Helps discover
entities, concepts, or related domain knowledge already
modeled in the system.

Depends on: knowledge_graph engine
"""

import logging
from typing import Any

from knowledge_graph.graph import get_knowledge_graph

logger = logging.getLogger(__name__)


async def search_knowledge_graph(
    arguments: dict[str, Any],
    user_context: dict[str, Any],
) -> dict[str, Any]:
    """
    arguments:
      term:        str  (required)
      max_results: int  (optional, default 10)

    returns:
      nodes: list[dict] — matched node id, label, type, related edges
      total: int
    """
    term        = arguments.get("term", "").strip()
    max_results = int(arguments.get("max_results", 10))

    if not term:
        raise ValueError("term is required")

    graph = get_knowledge_graph()
    nodes = graph.search_nodes(term=term, limit=max_results)

    logger.info(
        "mcp.search_knowledge_graph | Complete",
        extra={"term": term, "results": len(nodes)},
    )

    return {
        "nodes": [
            {
                "id":      n.id,
                "label":   n.label,
                "type":    n.type,
                "edges":   n.related_edges,
            }
            for n in nodes
        ],
        "total": len(nodes),
        "term":  term,
    }
