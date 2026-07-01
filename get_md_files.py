"""
get_md_files (Server 1 tool, per MCP.md spec)

Selects the most relevant markdown context files for a given
intent. Uses the knowledge graph to rank and pick documents
based on semantic relevance and token budget. Returns the
selected files, combined context, and token estimate.

Depends on: knowledge_graph engine, context_manager
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_graph.graph import get_knowledge_graph
from context_manager.manager import get_context_manager

logger = logging.getLogger(__name__)


async def get_md_files(
    db: AsyncSession,
    arguments: dict[str, Any],
    user_context: dict[str, Any],
) -> dict[str, Any]:
    """
    arguments:
      query:        str  (required) — user's natural language intent
      session_id:   str  (required) — conversation session
      token_budget: int  (optional) — max tokens for combined context

    returns:
      selected_files:   list[dict]  — file path + relevance score
      combined_context:  str        — concatenated md content
      token_estimate:    int
    """
    query        = arguments.get("query", "").strip()
    session_id   = arguments.get("session_id", "").strip()
    token_budget = int(arguments.get("token_budget", 4000))

    if not query:
        raise ValueError("query is required")
    if not session_id:
        raise ValueError("session_id is required")

    ctx_mgr = get_context_manager()
    graph   = get_knowledge_graph()

    # Load session so ranking can consider active entities
    session_state = await ctx_mgr.get_state(session_id)

    # Knowledge graph ranks and selects markdown files
    # within the token budget
    selection = graph.select_md_files(
        query=query,
        session_context=session_state,
        token_budget=token_budget,
    )

    logger.info(
        "mcp.get_md_files | Selected",
        extra={
            "session_id":  session_id,
            "files_count": len(selection.files),
            "tokens":      selection.token_estimate,
        },
    )

    return {
        "selected_files": [
            {
                "path":  f.path,
                "score": round(f.score, 4),
            }
            for f in selection.files
        ],
        "combined_context": selection.combined_context,
        "token_estimate":   selection.token_estimate,
        "session_id":       session_id,
    }
