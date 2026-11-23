"""Run with: python -m app.workers.worker"""

from redis import Redis
from rq import Worker

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    conn = Redis.from_url(settings.redis_url)
    worker = Worker(["locked-in"], connection=conn)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
