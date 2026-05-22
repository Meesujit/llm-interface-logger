import json, logging, os
from datetime import datetime
from typing import Any, Dict
import redis as redis_lib
from rq import Queue
from app.config import settings

logger = logging.getLogger(__name__)
FALLBACK_DIR = "/tmp/llm_logger_fallback"
os.makedirs(FALLBACK_DIR, exist_ok=True)
_redis_client = None
_queue = None

def _get_redis_client():
    global _redis_client
    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except Exception:
            _redis_client = None
    try:
        _redis_client = redis_lib.Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
        _redis_client.ping()
        return _redis_client
    except Exception as e:
        logger.warning("Redis unavailable (%s). Using fallback file logging.", e)
        return None

def _get_queue():
    global _queue
    client = _get_redis_client()
    if client is None: return None
    if _queue is None: _queue = Queue("inference_logs", connection=client)
    return _queue

def enqueue_log(log_payload: Dict[str, Any]):
    queue = _get_queue()
    if queue is not None:
        try:
            queue.enqueue("app.ingestion.pipeline.process_log", log_payload, job_timeout=30)
        except Exception as e:
            logger.warning("Failed to enqueue log (%s). Writing to fallback file.", e)
            _write_fallback(log_payload)
    else:
        _write_fallback(log_payload)

def _write_fallback(log_payload):
    try:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        with open(os.path.join(FALLBACK_DIR, f"log_{ts}.json"), "w") as f:
            json.dump(log_payload, f, default=str)
    except Exception as e:
        logger.error("Failed to write fallback log: %s", e)
