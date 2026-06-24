# SearXNG + Ollama Integration Guide

A complete, from-scratch guide covering every approach to integrate SearXNG as a web search tool with Ollama models.

---

## Prerequisites

Before anything, make sure you have:

- Docker installed
- Python 3.9+ installed
- Ollama installed and running (`ollama serve`)
- A model pulled that supports tool calling — `llama3.1`, `mistral`, `qwen2.5` are good choices

```bash
ollama pull llama3.1
```

---

## Step 1: Set Up SearXNG

### 1.1 — Run SearXNG via Docker

```bash
docker run -d \
  --name searxng \
  -p 8080:8080 \
  -e SEARXNG_SECRET_KEY="your_secret_key_here" \
  searxng/searxng
```

Verify it's running:

```bash
curl http://localhost:8080
```

### 1.2 — Enable JSON Format (Critical)

SearXNG blocks JSON responses by default. You must enable it.

Get inside the container:

```bash
docker exec -it searxng sh
```

Edit `/etc/searxng/settings.yml`:

```yaml
search:
  formats:
    - html
    - json       # <-- add this line
```

Restart the container:

```bash
docker restart searxng
```

Test JSON works:

```bash
curl "http://localhost:8080/search?q=test&format=json"
```

You should get a JSON response with a `results` array.

---

## Step 2: Python Environment Setup

Create a working directory and install dependencies:

```bash
mkdir ollama-searxng && cd ollama-searxng
pip install requests ollama openai
```

---

## Approach 1 — Simple Context Injection (No Tool Calling)

The most straightforward approach. You fetch results manually and inject them into the prompt as context. No special model support needed — works with any Ollama model.

### How it works

```
User query → You call SearXNG → Results injected into system prompt → Ollama answers
```

### Full working code

```python
# approach1_context_injection.py

import requests
import ollama

SEARXNG_URL = "http://localhost:8080/search"
OLLAMA_MODEL = "llama3.1"


def search_web(query: str, num_results: int = 5) -> str:
    """Fetch search results from SearXNG and return as plain text context."""
    try:
        response = requests.get(SEARXNG_URL, params={
            "q": query,
            "format": "json",
            "language": "en"
        }, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])[:num_results]

        if not results:
            return "No results found."

        context_lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            content = r.get("content", "No content")
            url = r.get("url", "")
            context_lines.append(f"[{i}] {title}\n    {content}\n    Source: {url}")

        return "\n\n".join(context_lines)

    except Exception as e:
        return f"Search failed: {str(e)}"


def ask_with_search(user_query: str) -> str:
    """Search the web and ask Ollama to answer using the results."""
    print(f"[*] Searching for: {user_query}")
    context = search_web(user_query)
    print(f"[*] Got context, sending to model...")

    system_prompt = f"""You are a helpful assistant with access to current web search results.
Use the following search results to answer the user's question accurately.
If the results don't contain enough information, say so.

Search Results:
{context}
"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    )

    return response["message"]["content"]


if __name__ == "__main__":
    query = "What are the latest developments in AI in 2025?"
    answer = ask_with_search(query)
    print("\n=== Answer ===")
    print(answer)
```

Run it:

```bash
python approach1_context_injection.py
```

### When to use this

- Model does not support tool calling
- You want simplicity and full control
- Latency is not a concern (you always search, even when not needed)

---

## Approach 2 — Tool Calling via Ollama Python SDK

The model decides *when* to search and *what* to search for. You define the tool, and the model calls it if needed.

### How it works

```
User query
    ↓
Model sees query + tool definition
    ↓
Model outputs a tool call (structured JSON)
    ↓
Your code runs the search
    ↓
Result sent back to model
    ↓
Model gives final answer
```

### Full working code

```python
# approach2_ollama_tool_calling.py

import requests
import ollama
import json

SEARXNG_URL = "http://localhost:8080/search"
OLLAMA_MODEL = "llama3.1"   # Must support tool calling


def search_web(query: str, num_results: int = 5) -> str:
    """Execute a SearXNG search and return formatted results."""
    try:
        response = requests.get(SEARXNG_URL, params={
            "q": query,
            "format": "json",
            "language": "en"
        }, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])[:num_results]
        if not results:
            return "No results found."

        lines = []
        for i, r in enumerate(results, 1):
            lines.append(
                f"[{i}] {r.get('title', '')}\n"
                f"    {r.get('content', '')}\n"
                f"    URL: {r.get('url', '')}"
            )
        return "\n\n".join(lines)

    except Exception as e:
        return f"Search error: {e}"


# Tool definition — tells the model what tools are available
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for current, real-time information. "
                "Use this when the user asks about recent events, news, "
                "or anything that requires up-to-date data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def run_tool(tool_name: str, tool_args: dict) -> str:
    """Dispatch tool calls to the right function."""
    if tool_name == "web_search":
        return search_web(
            query=tool_args["query"],
            num_results=tool_args.get("num_results", 5)
        )
    return f"Unknown tool: {tool_name}"


def chat_with_tools(user_query: str) -> str:
    """Run an agentic loop: model decides when to search, you execute it."""
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Use the web_search tool when you need current information."
        },
        {
            "role": "user",
            "content": user_query
        }
    ]

    # Agentic loop
    while True:
        print("[*] Calling model...")
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            tools=tools
        )

        message = response["message"]
        messages.append(message)   # append assistant's response to history

        # Check if model wants to call a tool
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            # No tool call — model gave a final text answer
            return message["content"]

        # Execute each tool the model requested
        for call in tool_calls:
            tool_name = call["function"]["name"]
            tool_args = call["function"]["arguments"]

            print(f"[*] Model called tool: {tool_name} with args: {tool_args}")
            result = run_tool(tool_name, tool_args)
            print(f"[*] Tool returned {len(result)} characters")

            # Append tool result back to messages
            messages.append({
                "role": "tool",
                "content": result
            })

        # Loop again — model will now use the tool result to answer


if __name__ == "__main__":
    query = "What is the current price of Bitcoin?"
    print(f"\nUser: {query}\n")
    answer = chat_with_tools(query)
    print(f"\nAssistant: {answer}")
```

Run it:

```bash
python approach2_ollama_tool_calling.py
```

---

## Approach 3 — Tool Calling via OpenAI-Compatible API

Ollama exposes an OpenAI-compatible endpoint at `http://localhost:11434/v1`. This lets you use the `openai` Python library directly — useful if you want portability across Ollama, vLLM, LM Studio, or any OpenAI-compatible backend.

### Full working code

```python
# approach3_openai_compatible.py

import requests
import json
from openai import OpenAI

SEARXNG_URL = "http://localhost:8080/search"

# Point OpenAI client at local Ollama
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"     # Ollama doesn't need a real key, but the field is required
)

MODEL = "llama3.1"


def search_web(query: str, num_results: int = 5) -> str:
    try:
        resp = requests.get(SEARXNG_URL, params={
            "q": query,
            "format": "json"
        }, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])[:num_results]

        if not results:
            return "No results found."

        return "\n\n".join(
            f"[{i}] {r.get('title', '')}: {r.get('content', '')} ({r.get('url', '')})"
            for i, r in enumerate(results, 1)
        )
    except Exception as e:
        return f"Error: {e}"


tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information and recent events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    }
]


def chat(user_query: str) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful assistant with web search access."},
        {"role": "user", "content": user_query}
    ]

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"   # Let model decide when to search
        )

        choice = response.choices[0]
        messages.append(choice.message)

        if choice.finish_reason == "stop":
            return choice.message.content

        if choice.finish_reason == "tool_calls":
            for call in choice.message.tool_calls:
                name = call.function.name
                args = json.loads(call.function.arguments)

                print(f"[*] Tool call: {name}({args})")
                result = search_web(**args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result
                })


if __name__ == "__main__":
    answer = chat("What are the top AI news stories this week?")
    print(f"\nAnswer:\n{answer}")
```

Run it:

```bash
python approach3_openai_compatible.py
```

### When to use this over Approach 2

- You want code that works across Ollama, vLLM (like your Stargate setup), LM Studio, OpenRouter with zero changes
- You're already using the OpenAI SDK elsewhere
- You need `tool_call_id` tracking for multi-tool conversations

---

## Approach 4 — LangChain + Ollama + SearXNG (Framework-Based)

LangChain wraps the entire agentic loop for you. Good for building larger pipelines with memory, multiple tools, or chains.

### Setup

```bash
pip install langchain langchain-ollama langchain-community
```

### Full working code

```python
# approach4_langchain.py

import requests
from langchain_ollama import ChatOllama
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

SEARXNG_URL = "http://localhost:8080/search"


@tool
def web_search(query: str) -> str:
    """Search the web for current information. Input should be a search query string."""
    try:
        resp = requests.get(SEARXNG_URL, params={
            "q": query,
            "format": "json"
        }, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])[:5]

        if not results:
            return "No results found."

        return "\n".join(
            f"{r.get('title', '')}: {r.get('content', '')}"
            for r in results
        )
    except Exception as e:
        return f"Search failed: {e}"


def build_agent():
    llm = ChatOllama(model="llama3.1")
    tools = [web_search]

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant with web search access."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


if __name__ == "__main__":
    agent = build_agent()
    result = agent.invoke({"input": "What happened in tech news today?"})
    print("\nAnswer:", result["output"])
```

Run it:

```bash
python approach4_langchain.py
```

---

## Quick Comparison

| | Approach 1 | Approach 2 | Approach 3 | Approach 4 |
|---|---|---|---|---|
| **Tool calling** | No | Yes | Yes | Yes |
| **Model decides when to search** | No | Yes | Yes | Yes |
| **Library** | `ollama` | `ollama` | `openai` | `langchain` |
| **Works with non-tool models** | ✅ | ❌ | ❌ | ❌ |
| **Portable across backends** | ❌ | ❌ | ✅ | Partial |
| **Best for** | Quick setup | Ollama-native | vLLM/multi-backend | Large pipelines |
| **Complexity** | Low | Medium | Medium | High |

---

## Troubleshooting

**SearXNG returns HTML instead of JSON**
→ Make sure `json` is listed under `search.formats` in `settings.yml` and the container was restarted.

**Model doesn't call the tool**
→ Some models need better tool descriptions. Be explicit: "Use this tool when asked about anything after 2023 or for current events."

**Model calls tool in a loop**
→ Add a `max_iterations` counter to your while loop and break after ~5 iterations.

**Ollama 404 on tool calls**
→ Your model may not support tools. Try `llama3.1`, `mistral-nemo`, or `qwen2.5`.

**Connection refused on port 8080**
→ Check Docker is running: `docker ps | grep searxng`

---

## Recommended Setup for Your Org

Given that you're running models on Ollama across your org:

1. **Deploy SearXNG on a shared internal server** (not localhost) so all Ollama clients can reach it
2. **Use Approach 3 (OpenAI-compatible)** — it gives you flexibility to swap Ollama for vLLM or other backends without rewriting your search integration
3. **Set `SEARXNG_BASE_URL` as an environment variable** so all services can point to the shared instance
