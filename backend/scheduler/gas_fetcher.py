# scheduler/gas_fetcher.py
"""
Fetch Etherscan gas-oracle data, cache it in Redis, and push alerts to
Telegram + X (formerly Twitter).

Key improvements
----------------
* MIN_DELTA_GWEI  – only alert if |ΔbaseFee| >= X Gwei
* MAX_SILENCE     – send a heartbeat after Y seconds of silence
* Existing debounce (MIN_EVENT_INTERVAL) still applies

Env-vars (with sane defaults)
-----------------------------
ETHERSCAN_API_KEY              (required)
REDIS_URL                = redis://localhost:6379
FEE_THRESHOLDS           = 1,2,3,5,8,12,20,35,60,100,200
MIN_EVENT_INTERVAL       = 60        # s  – short debounce
MIN_DELTA_GWEI           = 0.3       # Gwei
MAX_SILENCE              = 43200     # s  – 12 h heartbeat

# Optional for Telegram
TG_BOT_TOKEN
TG_CHAT_ID

# Optional for X
X_API_KEY
X_API_KEY_SECRET
X_ACCESS_TOKEN
X_ACCESS_TOKEN_SECRET
"""

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
from services.x_poster import post_to_x

load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
REDIS_URL         = os.getenv("REDIS_URL", "redis://localhost:6379")

# Redis keys
GAS_KEY           = "gas_fee"
LAST_FEE_KEY      = "last_base_fee"
THRESHOLD_KEY     = "gas_threshold_state"
THRESHOLD_TS_KEY  = f"{THRESHOLD_KEY}_time"
LAST_EVENT_TS_KEY = "gas_last_event_ts"     # for debounce / silence

# Tunables
MIN_EVENT_INTERVAL = int(os.getenv("MIN_EVENT_INTERVAL", "60"))        # s
MIN_DELTA_GWEI     = float(os.getenv("MIN_DELTA_GWEI",  "0.3"))        # Gwei
MAX_SILENCE        = int(os.getenv("MAX_SILENCE",       "43200"))      # s (12 h)

# Thresholds
_raw = os.getenv("FEE_THRESHOLDS", "1,2,3,5,8,12,20,35,60,100,200")
THRESHOLDS: list[float] = sorted({float(x) for x in _raw.split(",") if x.strip()})

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def iso_utc() -> str:
    """
    Return current time in ISO-8601, *always* tagged as UTC (…Z).
    Example: '2025-05-19T08:09:20Z'
    """
    return (
        datetime.now(timezone.utc)         # tz-aware datetime
        .isoformat(timespec="seconds")     # drop microseconds → 2025-05-19T08:09:20+00:00
        .replace("+00:00", "Z")            # RFC-3339 UTC short-hand
    )

# ───────────────────────── helpers ─────────────────────────
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


# ───────────────────────── main job ─────────────────────────
def fetch_and_cache_gas() -> None:
    try:
        result   = fetch_gas_oracle()
        curr_fee = float(result["suggestBaseFee"])
        block    = result["LastBlock"]

        prev_fee = float(redis_client.get(LAST_FEE_KEY) or curr_fee)
        delta    = curr_fee - prev_fee
        abs_delta = abs(delta)

        event       = detect_cross(prev_fee, curr_fee)
        now_ts      = time.time()
        last_ts_raw = redis_client.get(LAST_EVENT_TS_KEY)
        if last_ts_raw is None:
            redis_client.set(LAST_EVENT_TS_KEY, now_ts)
            return
        last_ts = float(last_ts_raw)

        allow_push  = (now_ts - last_ts) >= MIN_EVENT_INTERVAL
        must_push   = (now_ts - last_ts) >= MAX_SILENCE  # heartbeat trigger

        # ─── (1) threshold-cross alert ───
        if (
            event
            and abs_delta >= MIN_DELTA_GWEI   # big enough move
            and allow_push                    # debounce
        ):
            push_alert(
                curr_fee=curr_fee,
                prev_fee=prev_fee,
                delta=delta,
                block=block,
                event=event,
                is_heartbeat=False,
                result=result,
            )
            redis_client.set(LAST_EVENT_TS_KEY, now_ts)

        # ─── (2) daily heartbeat ───
        elif must_push:
            push_alert(
                curr_fee=curr_fee,
                prev_fee=prev_fee,
                delta=0.0,
                block=block,
                event=None,
                is_heartbeat=True,
                result=result,
            )
            redis_client.set(LAST_EVENT_TS_KEY, now_ts)

        # Persist latest fee
        redis_client.set(LAST_FEE_KEY, curr_fee)

        # Cache full snapshot
        redis_client.set(
            GAS_KEY,
            json.dumps(
                {
                    "safe":        f"{result['SafeGasPrice']} Gwei",
                    "propose":     f"{result['ProposeGasPrice']} Gwei",
                    "fast":        f"{result['FastGasPrice']} Gwei",
                    "base_fee":    f"{curr_fee:.6f} Gwei",
                    "last_block":  block,
                    "last_updated": iso_utc(),
                }
            ),
        )

        print(
            f"[INFO] Gas @ block {block} → {curr_fee:.6f} Gwei "
            f"(prev {prev_fee:.6f})"
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
    safe = fmt_gwei(float(result["SafeGasPrice"]))
    prop = fmt_gwei(float(result["ProposeGasPrice"]))
    fast = fmt_gwei(float(result["FastGasPrice"]))
    utc_ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    if is_heartbeat:
        tg_msg = (
            f"📊 Daily gas snapshot\n"
            f"• Base fee: {fmt_gwei(curr_fee)} Gwei\n"
            f"• Suggested prices:\n"
            f"   - Safe: {safe} Gwei\n"
            f"   - Propose: {prop} Gwei\n"
            f"   - Fast: {fast} Gwei\n"
            f"• Block: [#{block}](https://etherscan.io/block/{block})\n"
            f"• Time: {utc_ts}"
        )
        send_message(tg_msg)

        x_msg = (
            f"📊 Gas snapshot\n"
            f"Base {fmt_gwei(curr_fee)} Gwei\n"
            f"Safe {safe} | Prop {prop} | Fast {fast}\n"
            f"Blk {block}\n"
            f"#Ethereum #GasFees #ETHGas"
        )
        post_to_x(x_msg)
        return

    # threshold-cross message
    direction = "increased" if delta > 0 else "decreased"
    boundary  = "above" if event["state"] == "above" else "below"
    change    = f"{direction} by {abs(delta):.2f} Gwei"
    t_key     = event["threshold"]

    tg_msg = (
        f"⛽️ Gas fee {direction} {boundary} {t_key} Gwei\n"
        f"• Current base fee: {fmt_gwei(curr_fee)} Gwei ({change})\n"
        f"• Suggested prices:\n"
        f"   - Safe: {safe} Gwei\n"
        f"   - Propose: {prop} Gwei\n"
        f"   - Fast: {fast} Gwei\n"
        f"• Block: [#{block}](https://etherscan.io/block/{block})\n"
        f"• Time: {utc_ts}"
    )
    send_message(tg_msg)

    x_msg = (
        f"⛽️ Gas {direction} {boundary} {t_key} Gwei\n"
        f"Base {fmt_gwei(curr_fee)} Gwei ({change})\n"
        f"Safe {safe} | Prop {prop} | Fast {fast}\n"
        f"Blk {block}\n"
        f"#Ethereum #GasFees #ETHGas"
    )
    post_to_x(x_msg)


def start_scheduler() -> None:
    sched = BackgroundScheduler()
    sched.add_job(fetch_and_cache_gas, "interval", seconds=10, max_instances=1)
    sched.start()
