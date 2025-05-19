# backend/api/events.py

from fastapi import APIRouter
import redis
import os
import json
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
r = redis.Redis.from_url(REDIS_URL)

router = APIRouter()

@router.get("/events")
def get_gas_events():
    state = r.hgetall("gas_threshold_state")
    timestamps = r.hgetall("gas_threshold_state_time")

    result = []

    for key in state:
        threshold = float(key.decode("utf-8"))
        status = state[key].decode("utf-8")
        time = timestamps.get(key)
        result.append({
            "threshold": threshold,
            "state": status,
            "last_changed": time.decode("utf-8") if time else None
        })

    result.sort(key=lambda x: x["threshold"])

    return {
        "events": result
    }
