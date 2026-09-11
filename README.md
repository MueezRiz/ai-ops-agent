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

## Project Status

| Week | Focus | Status |
|------|-------|--------|
| 1 | Skeleton backend + basic chatbot | Done |
| 2 | Multi-tool agent + memory | Done |
| 3 | RAG pipeline | Upcoming |
| 4 | RAG tuning | Upcoming |
| 5 | LangGraph agent loop | Upcoming |
| 6 | Agent robustness | Upcoming |
| 7 | n8n automations | Upcoming |
| 8 | Production hardening | Upcoming |
| 9 | Deployment | Upcoming |
| 10 | Portfolio packaging | Upcoming |