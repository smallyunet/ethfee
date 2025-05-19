# backend/api/gas.py
from fastapi import APIRouter
import redis, os, json
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
r = redis.Redis.from_url(REDIS_URL)

@router.get("/gas")
def get_gas():
    cached = r.get("gas_fee")
    if cached:
        return json.loads(cached)
    return {"error": "Gas data not available yet"}
