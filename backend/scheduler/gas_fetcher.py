from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

import redis
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from services.telegram import send_message
from services.event_log import append_event
from services.eth_price import get_eth_price_usd, set_eth_price_usd
from services.gas_calc import calc_usd_cost

load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
REDIS_URL         = os.getenv("REDIS_URL", "redis://localhost:6379")

# Redis keys
GAS_KEY           = "gas_fee"
LAST_FEE_KEY      = "last_base_fee"
LAST_EVENT_TS_KEY = "gas_last_event_ts"
ETH_PRICE_KEY     = "eth_price_usd"

# Tunables
MIN_EVENT_INTERVAL = int(os.getenv("MIN_EVENT_INTERVAL", "60"))        # s
MIN_DELTA_GWEI     = float(os.getenv("MIN_DELTA_GWEI",  "0.3"))        # Gwei
MAX_SILENCE        = int(os.getenv("MAX_SILENCE",       "43200"))      # s
BIG_JUMP_GWEI      = float(os.getenv("BIG_JUMP_GWEI",   "5.0"))        # Gwei

# Thresholds
_raw = os.getenv("FEE_THRESHOLDS", "1,2,3,5,8,12,20,35,60,100,200")
THRESHOLDS: list[float] = sorted({float(x) for x in _raw.split(",") if x.strip()})

# Constants for gas limits
ETH_TRANSFER_GAS = 21000
USDT_TRANSFER_GAS = 65000

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def iso_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def fetch_gas_oracle() -> dict:
    url = "https://api.etherscan.io/api"
    params = {"module": "gastracker", "action": "gasoracle", "apikey": ETHERSCAN_API_KEY}
    data = requests.get(url, params=params, timeout=10).json()
    if data.get("status") != "1":
        raise RuntimeError(f"Etherscan error: {data.get('message')}")
    return data["result"]


def detect_cross(prev_fee: float, curr_fee: float) -> dict | None:
    down = [t for t in THRESHOLDS if prev_fee >= t > curr_fee]
    up   = [t for t in THRESHOLDS if prev_fee <= t < curr_fee]
    if down:
        return {"threshold": max(down), "state": "below"}
    if up:
        return {"threshold": min(up), "state": "above"}
    return None


def fmt_gwei(v: float) -> str:
    if v >= 10:
        return f"{v:.1f}"
    if v >= 1:
        return f"{v:.2f}"
    if v >= 0.1:
        return f"{v:.3f}"
    return f"{v:.4f}"


def fetch_and_cache_gas() -> None:
    try:
        result = fetch_gas_oracle()

        base_fee = float(result["suggestBaseFee"])
        propose_fee = float(result["ProposeGasPrice"])
        block = result["LastBlock"]

        prev_fee = float(redis_client.get(LAST_FEE_KEY) or base_fee)
        delta = base_fee - prev_fee
        abs_delta = abs(delta)
        event = detect_cross(prev_fee, base_fee)
        now_ts = time.time()
        last_ts = float(redis_client.get(LAST_EVENT_TS_KEY) or 0)

        allow_push = (now_ts - last_ts) >= MIN_EVENT_INTERVAL
        must_push = (now_ts - last_ts) >= MAX_SILENCE
        big_jump = abs_delta >= BIG_JUMP_GWEI

        should_push = (
            event and (
                big_jump or
                (abs_delta >= MIN_DELTA_GWEI and allow_push)
            )
        )

        if should_push:
            push_alert(
                curr_fee=propose_fee,
                prev_fee=prev_fee,
                delta=delta,
                block=block,
                event=event,
                is_heartbeat=False,
                result=result,
            )
            redis_client.set(LAST_EVENT_TS_KEY, now_ts)

        elif must_push:
            push_alert(
                curr_fee=propose_fee,
                prev_fee=prev_fee,
                delta=0.0,
                block=block,
                event=None,
                is_heartbeat=True,
                result=result,
            )
            redis_client.set(LAST_EVENT_TS_KEY, now_ts)

        redis_client.set(LAST_FEE_KEY, base_fee)

        eth_price_usd = get_eth_price_usd()

        eth_tx_usd = calc_usd_cost(propose_fee, eth_price_usd, ETH_TRANSFER_GAS)
        usdt_tx_usd = calc_usd_cost(propose_fee, eth_price_usd, USDT_TRANSFER_GAS)

        safe_fee = float(result["SafeGasPrice"])
        fast_fee = float(result["FastGasPrice"])

        redis_client.set(
            GAS_KEY,
            json.dumps(
                {
                    "safe": f"{safe_fee} Gwei",
                    "propose": f"{propose_fee} Gwei",
                    "fast": f"{fast_fee} Gwei",
                    "base_fee": f"{base_fee:.6f} Gwei",
                    "last_block": block,
                    "last_updated": iso_utc(),
                    "eth_price_usd": eth_price_usd,
                    "eth_transfer_usd": eth_tx_usd,
                    "usdt_transfer_usd": usdt_tx_usd,
                    "safe_transfer_usd": calc_usd_cost(safe_fee, eth_price_usd, ETH_TRANSFER_GAS),
                    "propose_transfer_usd": eth_tx_usd,
                    "fast_transfer_usd": calc_usd_cost(fast_fee, eth_price_usd, ETH_TRANSFER_GAS),
                }
            ),
        )

        print(
            f"[INFO] Gas @ block {block} → {propose_fee:.6f} Gwei "
            f"(base {base_fee:.6f}) | ETH ${eth_price_usd:.2f} | "
            f"ETH tx: ${eth_tx_usd:.4f}, USDT tx: ${usdt_tx_usd:.4f}"
        )

    except Exception as exc:
        print(f"[ERROR] fetch_and_cache_gas: {exc}")


def push_alert(
    *,
    curr_fee: float,
    prev_fee: float,
    delta: float,
    block: str,
    event: dict | None,
    is_heartbeat: bool,
    result: dict,
) -> None:
    eth_price_usd = get_eth_price_usd()
    eth_tx_usd = calc_usd_cost(curr_fee, eth_price_usd, ETH_TRANSFER_GAS)
    usdt_tx_usd = calc_usd_cost(curr_fee, eth_price_usd, USDT_TRANSFER_GAS)
    utc_ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    if is_heartbeat:
        msg = (
            f"📊 Current Ethereum base fee: {fmt_gwei(curr_fee)} Gwei\n"
            f"Estimated cost: ${eth_tx_usd:.4f} (ETH), ${usdt_tx_usd:.4f} (USDT)\n\n"
            f"Block: #{block}\n"
            f"Updated: {utc_ts}"
        )
        send_message(msg)
        return

    direction = "rose" if delta > 0 else "dropped"
    threshold = event["threshold"]
    msg = (
        f"⛽️ Gas fee just {direction} around {threshold} Gwei\n"
        f"Base fee: {fmt_gwei(curr_fee)} Gwei\n"
        f"Estimated cost: ${eth_tx_usd:.4f} (ETH), ${usdt_tx_usd:.4f} (USDT)\n\n"
        f"Block: #{block}\n"
        f"Updated: {utc_ts}"
    )
    send_message(msg)
    append_event(event["threshold"], event["state"], iso_utc())


def fetch_eth_price_and_cache() -> None:
    """Fetch ETH price from CoinGecko and cache in Redis"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "ethereum", "vs_currencies": "usd"}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        price = float(data["ethereum"]["usd"])
        redis_client.set(ETH_PRICE_KEY, price)
        redis_client.set("eth_price_last_updated", iso_utc())
        print(f"[INFO] Updated ETH price: ${price:.2f}")
    except Exception as e:
        print(f"[ERROR] fetch_eth_price_and_cache: {e}")


def start_scheduler() -> None:
    sched = BackgroundScheduler()
    sched.add_job(fetch_eth_price_and_cache, "interval", minutes=5, max_instances=1)
    sched.add_job(fetch_and_cache_gas, "interval", seconds=10, max_instances=1)
    sched.start()
    print("[INFO] Scheduler started.")
