import redis
import os
import json
from dotenv import load_dotenv
from typing import List

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

EVENT_LOG_KEY = "gas_event_log"


def append_event(threshold: float, state: str, timestamp: str) -> None:
    event = {
        "threshold": threshold,
        "state": state,
        "timestamp": timestamp,
    }
    redis_client.lpush(EVENT_LOG_KEY, json.dumps(event))
    redis_client.ltrim(EVENT_LOG_KEY, 0, 99)  # keep latest 100


def get_recent_events(limit: int = 50) -> List[dict]:
    raw = redis_client.lrange(EVENT_LOG_KEY, 0, limit - 1)
    return [json.loads(e) for e in raw]
