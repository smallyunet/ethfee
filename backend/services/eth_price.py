# backend/services/eth_price.py

import requests

def get_eth_price_usd() -> float:
    """Fetch ETH price from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "ethereum", "vs_currencies": "usd"}

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        return float(data["ethereum"]["usd"])
    except Exception as e:
        print(f"[ERROR] get_eth_price_usd: {e}")
        return 0.0
