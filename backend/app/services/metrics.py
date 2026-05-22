from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inference_log import InferenceLog

def _bucket_expr(window: str) -> str:
    if window in ("1h", "6h"):
        return "date_trunc('hour', created_at) + (FLOOR(EXTRACT(MINUTE FROM created_at) / 5) * 5) * INTERVAL '1 minute'"
    return "date_trunc('hour', created_at)"

async def get_metrics(db: AsyncSession, window: str = "24h"):
    now = datetime.now(timezone.utc)
    deltas = {"1h": timedelta(hours=1), "6h": timedelta(hours=6), "24h": timedelta(hours=24), "7d": timedelta(days=7)}
    since = now - deltas.get(window, timedelta(hours=24))

    total_q = select(func.count(InferenceLog.id)).where(InferenceLog.created_at >= since)
    total_requests = (await db.execute(total_q)).scalar() or 0
    error_q = select(func.count(InferenceLog.id)).where(InferenceLog.created_at >= since, InferenceLog.status == "error")
    error_count = (await db.execute(error_q)).scalar() or 0
    error_rate = (error_count / total_requests) if total_requests > 0 else 0.0
    mins = (now - since).total_seconds() / 60
    rpm = total_requests / max(mins, 1)

    latency_stats = await db.execute(text("""
        SELECT AVG(latency_ms) FILTER (WHERE status = 'success') as avg_latency,
        COALESCE(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms) FILTER (WHERE status = 'success'), 0) as p50,
        COALESCE(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) FILTER (WHERE status = 'success'), 0) as p95,
        COALESCE(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms) FILTER (WHERE status = 'success'), 0) as p99
        FROM inference_logs WHERE created_at >= :since
    """), {"since": since})
    row = latency_stats.fetchone()
    avg_lat = float(row[0]) if row and row[0] else 0.0
    p50_lat = float(row[1]) if row and row[1] else 0.0
    p95_lat = float(row[2]) if row and row[2] else 0.0
    p99_lat = float(row[3]) if row and row[3] else 0.0

    token_q = select(func.coalesce(func.sum(InferenceLog.total_tokens), 0)).where(InferenceLog.created_at >= since)
    total_tokens = (await db.execute(token_q)).scalar() or 0

    provider_stats = await db.execute(text("""
        SELECT provider, COUNT(*) as requests, AVG(latency_ms) FILTER (WHERE status = 'success') as avg_latency
        FROM inference_logs WHERE created_at >= :since GROUP BY provider
    """), {"since": since})
    by_provider = {}
    for r in provider_stats:
        by_provider[r[0]] = {"requests": r[1], "avg_latency_ms": float(r[2]) if r[2] else 0.0}

    bucket = _bucket_expr(window)
    latency_time = await db.execute(text(f"SELECT {bucket} as bucket, AVG(latency_ms) FILTER (WHERE status = 'success') as avg_latency FROM inference_logs WHERE created_at >= :since GROUP BY bucket ORDER BY bucket"), {"since": since})
    latency_over_time = [{"timestamp": r[0].isoformat() if r[0] else "", "avg_latency_ms": float(r[1]) if r[1] else 0.0} for r in latency_time]

    errors_time = await db.execute(text(f"SELECT {bucket} as bucket, COUNT(*) as error_count FROM inference_logs WHERE created_at >= :since AND status = 'error' GROUP BY bucket ORDER BY bucket"), {"since": since})
    errors_over_time = [{"timestamp": r[0].isoformat() if r[0] else "", "count": r[1]} for r in errors_time]

    return {
        "avg_latency_ms": round(avg_lat, 2), "p50_latency_ms": round(p50_lat, 2),
        "p95_latency_ms": round(p95_lat, 2), "p99_latency_ms": round(p99_lat, 2),
        "total_requests": total_requests, "error_rate": round(error_rate, 4),
        "requests_per_minute": round(rpm, 2), "total_tokens": total_tokens,
        "by_provider": by_provider, "latency_over_time": latency_over_time,
        "errors_over_time": errors_over_time,
    }
