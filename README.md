# AI Operations Agent

A portfolio project demonstrating an AI-powered customer service agent built with FastAPI, Ollama, and PostgreSQL. The agent handles customer queries for a fictional clothing brand — checking order statuses, creating support tickets, and escalating issues to human agents — with persistent conversation memory across sessions.

This is a learning/portfolio project built to demonstrate tool use, persistent memory, and (upcoming) RAG and agent loop patterns.

## Architecture

Requests come in via the `POST /chat` endpoint. The app loads the conversation history for that session from PostgreSQL, then sends the full message history to the LLM. The LLM decides whether to answer directly or call one of three tools (order status, ticket creation, escalation). If a tool is called, the result is fed back to the LLM which then generates a natural language reply. Every message is saved to Postgres so context persists across requests.

## Tech Stack

- FastAPI — backend API
- Ollama + qwen2.5 — local LLM, no API costs
- PostgreSQL — conversation and ticket storage
- ChromaDB — vector store for RAG (coming Week 3)
- LangGraph — agent loop (coming Week 5)
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

## Project Status

| Week | Focus | Status |
|------|-------|--------|
| 1 | Skeleton backend + basic chatbot | Done |
| 2 | Multi-tool agent + memory | Done |
| 3 | RAG pipeline | Done |
| 4 | RAG tuning | Upcoming |
| 5 | LangGraph agent loop | Upcoming |
| 6 | Agent robustness | Upcoming |
| 7 | n8n automations | Upcoming |
| 8 | Production hardening | Upcoming |
| 9 | Deployment | Upcoming |
| 10 | Portfolio packaging | Upcoming |