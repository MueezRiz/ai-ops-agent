# AI Operations Agent

A customer service chatbot for a fictional clothing brand built with FastAPI, 
LangGraph, and local LLMs via Ollama. The agent can answer FAQs using RAG, 
check order statuses, create support tickets, and escalate issues to humans — 
all running locally for free with no external API costs.

## Tech Stack
- FastAPI — backend API
- Ollama + Mistral — local LLM, no API costs
- PostgreSQL — conversation and ticket storage
- ChromaDB — vector store for RAG (coming Week 3)
- LangGraph — agent loop (coming Week 5)
- n8n — workflow automation (coming Week 7)
- Docker — containerization

## How to Run
1. Start Docker Desktop
2. Run `docker-compose up -d` to start Postgres
3. Run `ollama serve` in a terminal tab
4. Activate venv: `source venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Start the server: `uvicorn main:app --reload`
7. Hit the chat endpoint:
\```
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of order 123?"}'
\```