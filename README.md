# LLM Inference Logger

A lightweight inference logging and ingestion system for LLM applications. Chat with Groq or Gemini while every inference is captured, PII-redacted, and persisted for observability.

## Quick Start

```bash
git clone https://github.com/Meesujit/llm-interface-logger.git
cd llm-interface-logger
cp .env.example .env
```

Add your API keys to `.env`:

```
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AI...
```

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Chat UI | http://localhost:3000 |
| Dashboard | http://localhost:3000/dashboard |
| API docs | http://localhost:8000/docs |

Zero manual setup beyond adding API keys. One command, everything works.

## Architecture Overview

```
User → React UI (Vite :3000)
         │  HTTP / SSE
         ▼
    FastAPI (:8000)
         │
         ├── LLMLogger SDK ──► Groq / Gemini
         │
         ├── PostgreSQL 15 ──► conversations, messages, inference_logs
         │
         └── Redis 7 ──► RQ Worker ──► Ingestion Pipeline
                              │
                              ├── Validate payload
                              ├── Redact PII (Presidio)
                              ├── Enrich with timestamps
                              └── Store + update aggregates
```

**5 layers:**

| Layer | Tech | Purpose |
|-------|------|---------|
| Chatbot UI | React 18, Vite, Tailwind, Recharts | Multi-turn conversations with streaming |
| SDK Wrapper | Python `LLMLogger` class | Captures inference metadata before/after LLM calls |
| Ingestion Pipeline | Redis + RQ worker | Validates, redacts PII, enriches, stores |
| Database | PostgreSQL 15 | Conversations, messages, inference_logs |
| Dashboard | Recharts (Line, Bar, Area) | Latency, throughput, errors, provider breakdown |

## Ingestion Flow

1. User sends message → React frontend calls `POST /api/chat`
2. Backend wraps the LLM call in `LLMLogger` middleware
3. `LLMLogger` calls the provider (Groq/Gemini), captures start/end time, tokens, request ID
4. Response returned to user immediately — no blocking
5. After response, `LLMLogger` pushes log payload to Redis queue (fire-and-forget)
6. RQ Worker consumes the queue
7. Pipeline validates → redacts PII with Microsoft Presidio → enriches timestamps → stores in PostgreSQL
8. Dashboard queries `inference_logs` table for real-time metrics

## Logging Strategy

- **Immediate response, async logging**: User gets the LLM response first. Logs are queued in Redis and processed by a background worker. The chat endpoint never waits for log persistence.
- **Queue-backed**: Redis acts as a buffer. If the worker is slow, logs queue up without affecting response latency.
- **Fire-and-forget**: `LLMLogger.enqueue_log()` pushes to Redis and returns. No await, no blocking.
- **Structured payloads**: Every log has a well-defined Pydantic schema — provider, model, latency_ms, token counts, status, error details, input/output previews, raw metadata.
- **Error logs**: LLM failures are logged too — `status=error` with `error_type` and `error_message`.
- **Fallback**: If Redis is unreachable, logs are written to local JSON files at `/tmp/llm_logger_fallback/` so no data is lost.

## Schema Design Decisions

**Three core tables: `conversations`, `messages`, `inference_logs`**

- **conversations and messages are separate** — standard normalization. Messages can be paginated independently. Conversation metadata (status, message count, total tokens) is denormalized for fast listing.
- **inference_logs is separate from messages** — observability data should not be coupled to chat data. Logs can be sampled, archived, or moved to a different store without affecting the chat system.
- **JSONB `raw_metadata`** — captures provider-specific response headers (model fingerprint, timestamps) without schema changes. Flexible for new providers.
- **`input_preview` / `output_preview` capped at 300 chars** — reduces storage cost and PII exposure surface area. Full content lives in `messages`.
- **`sequence_num` on messages** — reliable ordering independent of timestamp drift or clock skew.
- **`folder_id` on conversations** — optional FK to `folders` table. Users can organize chats into folders without affecting the message flow.
- **Indexes on `created_at`, `provider`, `status`** — optimized for dashboard queries (time-window aggregations, provider breakdowns, error filtering).

## Tradeoffs Made

| Decision | Why |
|----------|-----|
| Redis + RQ over Kafka | Simpler ops for this scale (<1M logs/day). RQ needs no separate broker. Easy to swap later. |
| PostgreSQL over ClickHouse | Familiar, battle-tested. Good enough for <1M logs/day. Dashboard queries with `PERCENTILE_CONT` work fine. |
| SSE over WebSockets | Simpler protocol. One-directional streaming from LLM is all we need. No handshake complexity. |
| PII redaction in worker, not API | Keeps chat response latency low. User gets fast response, redaction happens async. |
| Sliding window of 10 messages | Balances context quality with token cost. Configurable limit. |
| Groq + Gemini over Claude + OpenAI | Both have generous free tiers. Good enough for demos. Provider abstraction makes swapping trivial. |
| `asyncpg` over `psycopg2` | True async I/O. Every database call is non-blocking in the FastAPI event loop. |

## What I Would Improve With More Time

- **ClickHouse for analytics at scale** — at >10M logs/day, PostgreSQL percentiles get slow. ClickHouse is purpose-built for this.
- **OpenTelemetry tracing** — distributed traces across frontend → backend → LLM → worker for end-to-end visibility.
- **Alert rules** — error rate > 5% triggers email/Slack via webhook.
- **Conversation search** — pgvector embeddings for semantic search across chat history.
- **Rate limiting** — per-user, per-session token buckets to prevent abuse.
- **Log sampling** — only log 10% of requests above a latency threshold for cost control.
- **Kafka migration** — guaranteed delivery, replay capability, better partitioning for high throughput.
- **Kubernetes Helm chart** — parameterized deployment with auto-scaling policies.
- **Authentication** — OAuth or API keys for multi-user access.

## Scaling Considerations

- **Horizontal scaling**: Backend and worker are stateless. Scale replicas behind a load balancer. Redis queue naturally distributes work.
- **Database**: PostgreSQL handles ~1M logs/day comfortably. Beyond that, partition `inference_logs` by month, add read replicas, or migrate to ClickHouse.
- **Redis**: Single instance handles ~100K enqueues/second. For higher throughput, use Redis Cluster.
- **Worker**: RQ workers can scale horizontally. Each worker picks up jobs independently from Redis.
- **PII redaction**: Presidio is CPU-bound. At high throughput, run dedicated redaction workers or batch-process.

## Failure Handling

- **LLM provider failure**: Caught in `LLMLogger`, logged as `status=error` with provider error details. Returned to user as 502 with clean message.
- **Redis unavailable**: Logs written to local fallback files at `/tmp/llm_logger_fallback/`. No data loss. Worker retries when Redis comes back.
- **Database unavailable**: Worker catches `DBAPIError`, logs the failure, and RQ retries the job. Backend returns 500 with error detail.
- **Worker crash**: RQ's default behavior retries failed jobs. Supervisor or Kubernetes restarts the worker pod.
- **PII redaction failure**: Falls back to storing unredacted text (logged warning). Presidio engine errors are caught at the module level.
- **Validation failure**: Invalid log payloads are caught by Pydantic. Pipeline logs the error and skips the record.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message, get LLM response |
| GET | `/api/chat/stream` | SSE streaming endpoint |
| GET | `/api/conversations` | List all conversations |
| GET | `/api/conversations/{id}` | Get single conversation |
| PATCH | `/api/conversations/{id}` | Rename, resume, move to folder |
| DELETE | `/api/conversations/{id}` | Cancel conversation |
| GET | `/api/conversations/{id}/messages` | Paginated messages |
| GET | `/api/logs` | List inference logs (filters: provider, status, dates) |
| GET | `/api/logs/metrics?window=24h` | Aggregated dashboard metrics |
| GET/POST | `/api/folders` | List/create folders |
| PATCH/DELETE | `/api/folders/{id}` | Rename/delete folders |

Full interactive docs at `http://localhost:8000/docs` after starting.

## Features

- **Multi-provider**: Groq (Llama 3.3 70B) + Gemini 2.0 Flash via abstract `BaseProvider`
- **Streaming**: SSE-based real-time token streaming with time-to-first-token tracking
- **Dashboard**: Latency line chart, provider bar chart, error area chart, stat cards, 30s auto-refresh
- **Docker Compose**: One command — `docker-compose up --build`
- **Event-based**: Redis queue + RQ worker for async, non-blocking log ingestion
- **PII redaction**: Microsoft Presidio (EMAIL, PHONE, CREDIT_CARD, SSN, PERSON, LOCATION)
- **Kubernetes**: Single-file manifest (`k8s/all.yaml`) + deploy script for self-hosted clusters
- **UI**: Cancel, resume, and list conversations. Folder organization with inline rename. Auto-title generation via LLM.

## Tech Stack

| Category | Technology |
|----------|-----------|
| Frontend | React 18, Vite, Tailwind CSS, Recharts, Zustand |
| Backend | Python 3.11, FastAPI, SQLAlchemy (async), Alembic |
| LLM Providers | Groq (Llama 3.3 70B), Google Gemini 2.0 Flash |
| Database | PostgreSQL 15 with asyncpg |
| Queue | Redis 7 + Python RQ |
| PII | Microsoft Presidio (analyzer + anonymizer) |
| NLP | spaCy (en_core_web_lg) |
| Containerization | Docker, Docker Compose |
| Orchestration | Kubernetes (optional, manifests included) |
