# MCP Servers Overview for Context OS

## Purpose

This project contains two Model Context Protocol (MCP) servers that act as the bridge between an AI assistant and the Context OS platform. They allow an AI client to interact with the system in a structured, tool-based way instead of relying only on raw text prompts.

In simple terms:
- MCP Server 1 handles orchestration, context retrieval, knowledge graph access, and agent execution.
- MCP Server 2 handles execution against connected data sources such as SQL databases, document stores, and other external systems.

These servers are designed so that an AI can do real work inside the platform: retrieve relevant documentation, reason over context, trigger agents, and run data queries.

---

## High-Level Architecture

Context OS is built around a workflow like this:

1. A user asks a question in natural language.
2. The system extracts intent and identifies the right context.
3. MCP Server 1 helps select the most relevant knowledge files and orchestrate internal agents.
4. MCP Server 2 can then run queries or inspect data sources when the task requires factual or operational execution.
5. The AI combines all of that into a final answer or action.

This means the MCP servers are not just “helper wrappers” — they are the practical interface that lets an AI operate on the platform’s knowledge and data.

---

## MCP Server 1: Orchestration

### Role

MCP Server 1 is the “planning and retrieval” server. It is responsible for helping the AI understand what context is relevant and what internal agents should be triggered.

### What it is for

Use this server when the AI needs to:
- find the best markdown context files for a task,
- search the knowledge graph,
- inspect the current session context for a user,
- kick off one or more agents,
- inspect agent health or progress,
- refresh the knowledge graph from markdown files.

### Exposed Tools

1. get_md_files
   - Selects the most relevant markdown context files for a given intent.
   - Uses the knowledge graph to rank and pick documents based on semantic relevance and token budget.
   - Returns the selected files, combined context, and token estimate.

2. run_agent
   - Starts a specific agent by ID.
   - Useful when the AI wants to invoke a single step in the workflow.

3. run_all_agents
   - Starts all agents in sequence.
   - Useful for full pipeline execution.

4. get_agent_status
   - Returns the status of one or all agents.
   - Helpful for monitoring progress or checking whether an agent has completed work.

5. search_knowledge_graph
   - Searches knowledge graph nodes by term.
   - Helps discover entities, concepts, or related domain knowledge already modeled in the system.

6. get_context
   - Retrieves the current context for a user and session.
   - Can provide the active entities, selected source, role, domain, and a context summary.

7. refresh_graph
   - Rebuilds the knowledge graph from markdown documents in the context_docs directory.
   - Useful after new documentation is added.

8. get_graph_stats
   - Returns summary statistics about the knowledge graph.

### Internal Dependencies

This server depends on:
- the knowledge graph engine,
- the context manager,
- the agent runner.

### Why it matters

This server makes the AI aware of the platform’s internal memory and reasoning structure. It is the layer that connects the AI to the company’s curated domain understanding.

---

## MCP Server 2: Data Execution

### Role

MCP Server 2 is the “execution and data access” server. It is responsible for interacting with registered data sources and running concrete operations like queries and schema inspection.

### What it is for

Use this server when the AI needs to:
- run SQL or data queries,
- inspect a source schema,
- preview table data,
- search document-based sources,
- test a connection,
- list registered data sources.

### Exposed Tools

1. execute_query
   - Executes a SQL or data query against a connected source.
   - Supports a source parameter, optional parameters, and row limit handling.
   - This is the main tool for operational data retrieval.

2. search_docs
   - Searches documents in a connected source such as SharePoint, S3, or similar document repositories.
   - Useful when the task requires semantic document search rather than direct SQL access.

3. get_schema
   - Retrieves the schema for a source or topic.
   - Helpful for understanding what tables or structures exist before querying.

4. preview_data
   - Pulls sample rows from a table.
   - Limits output to small samples for inspection.

5. list_sources
   - Lists all registered data sources and shows whether they are enabled.

6. test_connection
   - Verifies connectivity to a specific source.

### Internal Dependencies

This server depends on a connector registry. Each connector is a modular adapter for a specific data source.

### Why it matters

This server turns the AI from a passive assistant into an active executor. It can move from “understanding” to “doing” by interacting with real systems.

---

## How the Two Servers Work Together

The two MCP servers complement each other:

- MCP Server 1 is about context, orchestration, and knowledge.
- MCP Server 2 is about execution, querying, and data access.

A typical workflow might look like this:

1. The AI uses Server 1 to identify relevant markdown files or knowledge graph nodes.
2. The AI uses Server 1 to trigger specific agents for deeper reasoning.
3. If the question requires real data, the AI uses Server 2 to query a connected source.
4. The final answer is synthesized from the context and the executed results.

In other words:
- Server 1 answers “What should I consider?”
- Server 2 answers “What does the data say?”

---

## Design Philosophy

These MCP servers are intentionally built to be:

- modular,
- extensible,
- tool-driven,
- AI-friendly,
- source-agnostic.

The second server, in particular, is designed so that new data sources can be added without changing the core MCP interface. This makes it easy to connect new systems over time.

---

## What an AI Should Understand About These Servers

If another AI is being given this repository or these servers, it should understand the following:

- These are not just documentation endpoints; they are operational tool interfaces.
- They expose structured actions that an AI can call directly.
- Server 1 is the orchestration and knowledge layer.
- Server 2 is the execution and data layer.
- The system is designed for context-aware, tool-using reasoning rather than simple chat-only interaction.

A strong mental model is:
- “Context OS provides knowledge + agents + data access through MCP.”

---

## Recommended Interpretation for Another AI

When working with this project, another AI should treat these servers as the primary operational API surface for the platform.

It should:
- use Server 1 first when it needs relevant context, graph access, or internal agent orchestration,
- use Server 2 when it needs live data retrieval or source inspection,
- prefer the structured tool responses over trying to infer everything from free-form text alone.

---

## Summary

These two MCP servers make Context OS usable by AI agents in a practical and structured way.

- MCP Server 1 gives the AI access to domain context, knowledge retrieval, and workflow orchestration.
- MCP Server 2 gives the AI access to real data sources and execution capabilities.

Together, they form the operational backbone for AI-driven analysis and action inside the Context OS environment.
