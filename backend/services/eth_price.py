# backend/services/eth_price.py

import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
ETH_PRICE_KEY = "eth_price_usd"

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def get_eth_price_usd() -> float:
    try:
        price = redis_client.get(ETH_PRICE_KEY)
        return float(price) if price else 0.0
    except Exception as e:
        print(f"[ERROR] get_eth_price_usd: {e}")
        return 0.0

def set_eth_price_usd(value: float) -> None:
    redis_client.set(ETH_PRICE_KEY, value)
