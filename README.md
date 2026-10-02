# AI Operations Agent

A portfolio project demonstrating an AI-powered customer service agent built with FastAPI, Ollama, and PostgreSQL. The agent handles customer queries for a fictional clothing brand — checking order statuses, creating support tickets, and escalating issues to human agents — with persistent conversation memory across sessions.

This is a learning/portfolio project built to demonstrate tool use, persistent memory, RAG, and agent loop patterns.

## Architecture

Requests come in via the `POST /chat` endpoint. The app loads the conversation history for that session from PostgreSQL, then sends the full message history to the LLM. The LLM decides whether to answer directly or call one of three tools (order status, ticket creation, escalation). If a tool is called, the result is fed back to the LLM which then generates a natural language reply. Every message is saved to Postgres so context persists across requests.

## Tech Stack

- FastAPI — backend API
- Ollama + qwen2.5 — local LLM, no API costs
- PostgreSQL — conversation and ticket storage
- ChromaDB — vector store for RAG
- LangGraph — agent loop
- n8n — workflow automation (coming Week 7)
- Docker — containerization

## How to Run

1. Start Docker Desktop
2. Run `docker-compose up -d` to start Postgres
3. Run `ollama serve` in a separate terminal tab
4. Activate venv: `source venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Start the server: `uvicorn main:app --reload`
7. Hit the chat endpoint:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of order 123?"}'
```

## How RAG Works in This Project

The knowledge base is split into chunks of roughly 200-400 tokens using LangChain's text splitter. Each chunk is converted into a vector embedding and stored in a local Chroma database by running `ingest.py`. When a user sends a message, the query is embedded and compared against all stored chunks — the top 3 most relevant chunks are retrieved and injected into the system prompt before the LLM is called. If no chunks score above the relevance threshold, the bot responds with a fallback message instead of guessing.

## RAG Architecture

When a user asks a question, the chatbot retrieves relevant information from a local knowledge base before calling the LLM — this keeps answers grounded in real business data rather than relying on the model's general knowledge.

### How it works

**1. Ingestion (`ingest.py`)**
The knowledge base (FAQ entries in `knowledge_base.json`) is split into chunks of ~300 tokens using LangChain's text splitter. Each chunk is embedded using `nomic-embed-text` via Ollama and stored in a persistent ChromaDB collection.

**2. Retrieval (`retriever.py`)**
On each `/chat` request, the user's query is embedded and compared against the knowledge base using vector similarity search. The top 10 candidates are retrieved, then filtered by a distance threshold (0.7) to cut off low-confidence matches.

**3. Keyword boosting**
Chunks containing exact keywords from the query are promoted to the front of the candidate list before re-ranking. This prevents purely semantic search from missing obvious exact-match answers.

**4. Re-ranking**
A second LLM call (qwen2.5 via Ollama) acts as a relevance judge — it reads the top candidates and returns the 3 most relevant in order. This two-stage approach (broad retrieval → LLM scoring) consistently outperformed single-stage top-3 retrieval on test questions.

**5. Fallback**
If all retrieved chunks fall above the distance threshold (no confident match), the bot responds that it doesn't have that information rather than hallucinating an answer.

### Results
10/10 test questions answered correctly with the full pipeline. See [`rag_test_questions.md`](rag_test_questions.md) for full details.

## Agent Architecture

The agent is built as a LangGraph state graph with three nodes: **retrieve → decide → call_tool**, looping back from `call_tool` to `decide` until no further tool calls are needed.

On each `/chat` request, the graph first retrieves relevant FAQ context (retrieve node), then asks the LLM whether to answer directly or call a tool (decide node). If a tool is selected, it's executed and the result is appended to the message history before routing back to decide — allowing the agent to chain multiple tool calls in a single turn (e.g. check an order status, then create a ticket if it's delayed). When the LLM produces a response with no tool call, the graph exits and returns `final_response`.

The agent graph diagram is in [`/docs/agent-graph.png`](docs/agent-graph.png).

## Reliability & Error Handling

**Tool exceptions** are caught inside `call_tool_node` — if a tool raises an exception (e.g. a DB failure or bad input), the error is logged and a clean error string is returned as the tool result. The agent then generates a graceful natural language response rather than crashing or returning a 500.

**Retry logic** handles malformed tool calls. If the LLM calls a tool with missing required arguments, a `ToolMessage` error is injected back into the message history and the graph routes to decide again, giving the LLM one chance to self-correct with the full error context. The retry count is tracked in agent state to prevent infinite loops.

**Escalation to database** is real, not mocked — calling `escalate_to_human` inserts a row into the `tickets` table with `status = needs_review`. A separate script (`check_escalations.py`) queries and prints all open escalations.

**Logging** uses Python's `logging` module via `logger.py`. Every tool call, routing decision, retry attempt, and error is written to `logs/app.log` with a timestamp, making it straightforward to trace exactly what the agent did on any given request.

## Project Status

| Week | Focus                        | Status   |
|------|------------------------------|----------|
| 1    | Skeleton backend + basic chatbot | ✅ Done |
| 2    | Multi-tool agent + memory    | ✅ Done  |
| 3    | RAG pipeline                 | ✅ Done  |
| 4    | RAG tuning                   | ✅ Done  |
| 5    | LangGraph agent loop         | ✅ Done  |
| 6    | Agent robustness             | ✅ Done  |
| 7    | n8n automations              | Upcoming |
| 8    | Production hardening         | Upcoming |
| 9    | Deployment                   | Upcoming |
| 10   | Portfolio packaging          | Upcoming |