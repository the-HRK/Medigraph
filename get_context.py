"""
get_context (Server 1 tool, per MCP.md spec)

Retrieves the current context for a user and session.
Provides active entities, selected source, role, domain,
and a context summary.

Depends on: context_manager
"""

import logging
from typing import Any

from context_manager.manager import get_context_manager

logger = logging.getLogger(__name__)


async def get_context(
    arguments: dict[str, Any],
    user_context: dict[str, Any],
) -> dict[str, Any]:
    """
    arguments:
      session_id: str (required)

    returns:
      active_entities:  list[str]
      selected_source:  str
      role:             str
      domain:           str
      context_summary:  str
    """
    session_id = arguments.get("session_id", "").strip()
    if not session_id:
        raise ValueError("session_id is required")

    ctx_mgr = get_context_manager()
    state   = await ctx_mgr.get_state(session_id)

    if not state:
        return {
            "session_id":      session_id,
            "active_entities": [],
            "selected_source": "",
            "role":            user_context.get("roles", ["user"])[0],
            "domain":          "",
            "context_summary": "",
            "exists":          False,
        }

    summary = await ctx_mgr.build_llm_context(session_id)

    return {
        "session_id":      session_id,
        "active_entities": state.get("active_tables", []),
        "selected_source": state.get("connector_id", ""),
        "role":            user_context.get("roles", ["user"])[0],
        "domain":          state.get("last_intent", ""),
        "context_summary": summary,
        "exists":          True,
        }
