# Incident Copilot

Enterprise GenAI copilot for production incident management. Powered by Claude
(Anthropic) with RAG over historical incidents stored in PostgreSQL + pgvector.

## Prerequisites
- Docker + Docker Compose
- Anthropic API key
- Voyage AI API key (free tier works)

## Setup

1. Clone the repo
2. `cp .env.example .env` — fill in ANTHROPIC_API_KEY and VOYAGE_API_KEY
3. `docker compose up --build`
4. Backend seeds 20 mock incidents on first start (takes ~30s for embeddings)
5. Open http://localhost:5173

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/chat | Streaming chat (SSE) |
| POST | /api/rca/generate | Generate RCA report |
| GET | /api/incidents | List all incidents |
| GET | /api/incidents/{id} | Get incident + RCA |
| POST | /api/incidents/{id}/approve | Create approval request |
| PATCH | /api/incidents/{id}/approve/{aid} | Approve or reject |

## Architecture
- FastAPI backend with async SQLAlchemy and pgvector for semantic search
- Claude claude-sonnet-4-20250514 for chat and RCA generation via streaming SSE
- Voyage AI voyage-3 embeddings (dim=1024) stored in PostgreSQL
- React + Tailwind single-page frontend with real-time streaming UI
