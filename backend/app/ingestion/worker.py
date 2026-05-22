import logging, sys
import redis as redis_lib
from rq import Connection, Worker
from app.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger("worker")

def main():
    logger.info("Starting RQ worker...")
    redis_conn = redis_lib.Redis.from_url(settings.redis_url)
    with Connection(redis_conn):
        worker = Worker(queues=["inference_logs"], name="llm-logger-worker")
        logger.info("Worker initialized. Listening on queue: inference_logs")
        worker.work(with_scheduler=False)

if __name__ == "__main__":
    main()
