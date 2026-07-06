# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

TripAgent is an AI-powered travel planning agent built on **LangGraph**. Users describe travel needs in natural language; the Agent autonomously invokes multiple tools (attraction search, weather, route planning, restaurant search), performs multi-step reasoning via a ReAct loop, and outputs a complete travel itinerary. The frontend is built with **Streamlit** and includes real-time reasoning trace visualization.

## Tech stack

- **Agent framework**: LangGraph (`StateGraph`), LangChain tools (`@tool` decorator)
- **LLM**: DeepSeek Chat API via `langchain-deepseek`
- **Frontend**: Streamlit (wide layout, chat interface, reasoning trace sidebar)
- **RAG**: Custom `HybridRetriever` (keyword matching V1, designed for future BM25 + embedding upgrade)
- **Testing**: pytest

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app (requires DEEPSEEK_API_KEY in .env)
cd src && streamlit run main.py

# Run unit tests only (no API key needed)
pytest tests/test_tools.py -v -k "not AgentIntegration"

# Run all tests (requires DEEPSEEK_API_KEY set)
pytest tests/test_tools.py -v
```

## Architecture

The Agent follows a **ReAct (Reasoning + Acting) loop** driven by LangGraph's `StateGraph`:

```
User input → [agent node: LLM decides] → conditional edge → [tools node: execute] → back to agent → ... → END
```

### Key files

| File | Role |
|------|------|
| [src/agent/graph.py](src/agent/graph.py) | **Core**: Builds the `StateGraph`, binds 4 tools to the LLM, implements the agent/tools nodes and the conditional routing edge (`should_continue`) |
| [src/agent/state.py](src/agent/state.py) | `AgentState` TypedDict: `messages` (auto-append via `add_messages`), `next_step`, `travel_plan` |
| [src/agent/prompts.py](src/agent/prompts.py) | Layered system prompt: role → workflow → output format constraints → rules |
| [src/main.py](src/main.py) | Streamlit entry: dual-column layout (chat + reasoning trace sidebar), multi-turn memory, streaming output |
| [src/tools/attractions.py](src/tools/attractions.py) | `search_attractions` tool — Mock data for Beijing (5) and Hangzhou (3), keyword filtering, kid-friendly tag |
| [src/tools/weather.py](src/tools/weather.py) | `get_weather` tool — wttr.in API with timeout/error fallback messages |
| [src/tools/route.py](src/tools/route.py) | `plan_route` tool — 13 hardcoded attraction coordinates, approximate distance calc, transport recommendation (walk/metro/taxi) |
| [src/tools/restaurants.py](src/tools/restaurants.py) | `search_restaurants` tool — Mock data (Beijing 6, Hangzhou 5), filterable by nearby spot and budget level |
| [src/rag/retriever.py](src/rag/retriever.py) | `HybridRetriever` class — keyword-based TF scoring, loads from `data/attractions.json` or falls back to built-in data |
| [src/rag/data/attractions.json](src/rag/data/attractions.json) | 8-attraction knowledge base (structured JSON with title, city, type, duration, price, kid_friendly, content) |

### Agent flow

1. **agent node** (`agent_node`): On first call, injects `SYSTEM_PROMPT` as a `SystemMessage`. Invokes the LLM with bound tools. Catches API failures and returns a user-friendly error message.
2. **Conditional edge** (`should_continue`): If the LLM's response contains `tool_calls`, route to `tools` node; otherwise route to `END`.
3. **tools node** (`ToolNode`): LangGraph's built-in executor that parses the `tool_calls` and invokes the corresponding `@tool`-decorated function.
4. Loop back to `agent` node for further reasoning, repeating until the LLM decides no more tools are needed.

### Tool design pattern

Each tool uses the `@tool` decorator with Google-style docstrings. LangChain auto-generates the function schema (name, description, parameter types) from the decorator and docstring — this is how the LLM knows when and how to call each tool.

### Reasoning trace visualization

`main.py` uses `stream_mode="values"` to intercept each graph step. It classifies messages into tool-call events (`AIMessage` with `tool_calls`), tool-return events (`ToolMessage`), and final replies (`AIMessage` with `content`). These are rendered in the sidebar as expandable step cards.

### Multi-turn memory

The entire message history is passed into each `agent.stream()` call. LangGraph's `add_messages` reducer handles appending new messages to the existing list automatically.
