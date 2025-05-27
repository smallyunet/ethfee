# backend/scheduler/eth_price_fetcher.py

import os
import redis
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
ETH_PRICE_KEY = "eth_price_usd"
ETH_PRICE_UPDATED_KEY = "eth_price_last_updated"

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def fetch_eth_price() -> None:
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "ethereum", "vs_currencies": "usd"}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        price = float(data["ethereum"]["usd"])

        redis_client.set(ETH_PRICE_KEY, price)
        redis_client.set(ETH_PRICE_UPDATED_KEY, datetime.utcnow().isoformat())
        print(f"[INFO] Updated ETH price: ${price:.2f}")
    except Exception as e:
        print(f"[ERROR] fetch_eth_price: {e}")
