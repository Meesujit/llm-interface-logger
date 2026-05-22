# LLM Inference Logger

Chat with Groq and Gemini. Every inference is logged with latency, tokens, errors, and PII redaction.

## Quick Start

```bash
cp .env.example .env
# add GROQ_API_KEY and GEMINI_API_KEY
docker-compose up --build
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- Dashboard: http://localhost:3000/dashboard

## Stack

React 18 + Vite + Tailwind + Recharts | FastAPI + SQLAlchemy + Alembic | Groq (Llama 3.3) + Gemini 2.0 Flash | PostgreSQL 15 | Redis 7 + RQ | Microsoft Presidio | Docker Compose / Kubernetes

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message, get LLM response |
| GET | `/api/chat/stream` | SSE streaming |
| GET | `/api/conversations` | List conversations |
| PATCH | `/api/conversations/{id}` | Rename, move to folder, resume |
| DELETE | `/api/conversations/{id}` | Cancel |
| GET | `/api/logs` | Inference logs |
| GET | `/api/logs/metrics?window=24h` | Dashboard metrics |
| GET/POST/PATCH/DELETE | `/api/folders` | Folder CRUD |

## Kubernetes

```bash
./k8s/deploy.sh
```
