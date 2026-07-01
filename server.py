"""
Context OS — Single MCP Server
Port: 8001

Exposes all 9 tools defined in MCP.md, split conceptually
into "orchestration" and "execution" groups but served from
ONE process, ONE port, ONE auth layer.

Removed from MCP per production review (see admin.py instead):
  run_agent, run_all_agents, get_agent_status,
  refresh_graph, get_graph_stats
These are system maintenance operations, not AI-client-driven
actions, and are exposed as plain REST admin endpoints.

Depends on:
  knowledge_graph engine, context_manager, connector registry
"""

import json
import logging
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

from config import get_settings
from database import enable_pgvector, get_db_context
from utils.logging import setup_logging

from mcp.shared.middleware import mcp_auth_middleware
from mcp.shared.security import check_rate_limit, check_tool_permission

from mcp.tools.get_md_files import get_md_files
from mcp.tools.search_knowledge_graph import search_knowledge_graph
from mcp.tools.get_context import get_context
from mcp.tools.execute_query import execute_query
from mcp.tools.search_docs import search_docs
from mcp.tools.get_schema import get_schema
from mcp.tools.preview_data import preview_data
from mcp.tools.list_sources import list_sources
from mcp.tools.test_connection import test_connection

logger   = logging.getLogger(__name__)
settings = get_settings()

_current_request: ContextVar = ContextVar("current_request")

# ── Tool Definitions ──────────────────────────────────────────

TOOLS = [
    Tool(
        name="get_md_files",
        description=(
            "Select the most relevant markdown context files for a "
            "given intent. Uses the knowledge graph to rank and pick "
            "documents based on semantic relevance and token budget. "
            "ALWAYS call this first before reasoning about the "
            "platform's data or generating SQL."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query":        {"type": "string"},
                "session_id":   {"type": "string"},
                "token_budget": {"type": "integer", "default": 4000},
            },
            "required": ["query", "session_id"],
        },
    ),
    Tool(
        name="search_knowledge_graph",
        description=(
            "Search knowledge graph nodes by term. Discover entities, "
            "concepts, or related domain knowledge already modeled "
            "in the system."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "term":        {"type": "string"},
                "max_results": {"type": "integer", "default": 10},
            },
            "required": ["term"],
        },
    ),
    Tool(
        name="get_context",
        description=(
            "Retrieve the current context for a user and session — "
            "active entities, selected source, role, domain, and a "
            "context summary."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
            },
            "required": ["session_id"],
        },
    ),
    Tool(
        name="execute_query",
        description=(
            "Execute a SQL or data query against a connected source. "
            "Main tool for operational data retrieval. Supports a "
            "source parameter, optional bind parameters, and row "
            "limit handling."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "source":     {"type": "string"},
                "query":      {"type": "string"},
                "params":     {"type": "object"},
                "row_limit":  {"type": "integer", "default": 1000},
                "session_id": {"type": "string"},
            },
            "required": ["source", "query"],
        },
    ),
    Tool(
        name="search_docs",
        description=(
            "Search documents in a connected source such as "
            "SharePoint, S3, or similar document repositories. Use "
            "when the task requires semantic document search rather "
            "than direct SQL access."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "query":  {"type": "string"},
                "limit":  {"type": "integer", "default": 5},
            },
            "required": ["source", "query"],
        },
    ),
    Tool(
        name="get_schema",
        description=(
            "Retrieve the schema for a source or topic. Call this "
            "before execute_query to understand what tables or "
            "structures exist."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "topic":  {"type": "string"},
            },
            "required": ["source"],
        },
    ),
    Tool(
        name="preview_data",
        description=(
            "Pull sample rows from a table for inspection. Output "
            "is limited to small samples."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "table":  {"type": "string"},
                "limit":  {"type": "integer", "default": 5},
            },
            "required": ["source", "table"],
        },
    ),
    Tool(
        name="list_sources",
        description=(
            "List all registered data sources and show whether "
            "they are enabled."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="test_connection",
        description="Verify connectivity to a specific data source.",
        inputSchema={
            "type": "object",
            "properties": {"source": {"type": "string"}},
            "required": ["source"],
        },
    ),
]

TOOL_HANDLERS = {
    "get_md_files":           get_md_files,
    "search_knowledge_graph": search_knowledge_graph,
    "get_context":            get_context,
    "execute_query":          execute_query,
    "search_docs":            search_docs,
    "get_schema":             get_schema,
    "preview_data":           preview_data,
    "list_sources":           list_sources,
    "test_connection":        test_connection,
}

# Tools that need a DB session injected
NEEDS_DB = {"get_md_files", "list_sources"}

# ── MCP Server Instance ───────────────────────────────────────

mcp = Server("context-os")


@mcp.list_tools()
async def list_tools() -> ListToolsResult:
    return ListToolsResult(tools=TOOLS)


@mcp.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """
    Central dispatcher. Applies RBAC + rate limiting before
    every tool call, then routes to the handler.
    """
    request = _current_request.get(None)
    user_context = (
        getattr(request.state, "user_context", None)
        if request else None
    ) or {"user_id": "unknown", "org_id": "unknown", "roles": []}

    logger.info(
        "mcp.server | Tool called",
        extra={"tool": name, "user_id": user_context.get("user_id")},
    )

    try:
        check_tool_permission(user_context, name)
        await check_rate_limit(user_context.get("user_id"), name)

        handler = TOOL_HANDLERS.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")

        if name in NEEDS_DB:
            async with get_db_context() as db:
                result = await handler(db, arguments, user_context)
        else:
            result = await handler(arguments, user_context)

        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps(result, default=str, indent=2),
            )],
            isError=False,
        )

    except ValueError as e:
        logger.warning(
            "mcp.server | Validation error",
            extra={"tool": name, "error": str(e)},
        )
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "error": "validation_error",
                    "message": str(e),
                }),
            )],
            isError=True,
        )

    except Exception as e:
        logger.error(
            "mcp.server | Unexpected error",
            extra={"tool": name, "error": str(e)},
            exc_info=True,
        )
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "error": "internal_error",
                    "message": "An error occurred. Please try again.",
                }),
            )],
            isError=True,
        )


# ── FastAPI App ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(
        "mcp.server | Starting Context OS MCP Server",
        extra={"port": settings.MCP_SERVER_PORT},
    )
    async with get_db_context() as db:
        await enable_pgvector(db)
    logger.info("mcp.server | Ready — %d tools registered", len(TOOLS))
    yield
    logger.info("mcp.server | Shutting down")


fastapi_app = FastAPI(
    title="Context OS MCP Server",
    version="1.0.0",
    description="Single MCP server exposing orchestration and execution tools.",
    lifespan=lifespan,
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@fastapi_app.middleware("http")
async def _auth(request: Request, call_next):
    _current_request.set(request)
    return await mcp_auth_middleware(request, call_next)


transport = SseServerTransport("/mcp/messages")


@fastapi_app.get("/mcp/sse")
async def mcp_sse(request: Request):
    async with transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp.run(streams[0], streams[1], mcp.create_initialization_options())


@fastapi_app.post("/mcp/messages")
async def mcp_messages(request: Request):
    await transport.handle_post_message(
        request.scope, request.receive, request._send
    )


@fastapi_app.get("/health")
async def health():
    from database import check_db_health
    from connectors.registry import get_registry
    db_health = await check_db_health()
    registry  = get_registry()
    return {
        "status":     "healthy",
        "server":     "context-os-mcp",
        "tools":      len(TOOLS),
        "connectors": len(registry),
        "database":   db_health["status"],
    }


@fastapi_app.get("/tools")
async def list_tools_http():
    return {
        "tools": [
            {"name": t.name, "description": t.description}
            for t in TOOLS
        ]
}
