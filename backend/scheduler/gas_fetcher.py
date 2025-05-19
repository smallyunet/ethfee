# scheduler/gas_fetcher.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from dotenv import load_dotenv
import json
import os
import time
import redis
import requests

from services.telegram import send_message

load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
REDIS_URL         = os.getenv("REDIS_URL", "redis://localhost:6379")

# Redis keys
GAS_KEY            = "gas_fee"
LAST_FEE_KEY       = "last_base_fee"
THRESHOLD_KEY      = "gas_threshold_state"
THRESHOLD_TS_KEY   = f"{THRESHOLD_KEY}_time"
LAST_EVENT_TS_KEY  = "gas_last_event_ts"     # for debounce

# Debounce interval (seconds)
MIN_EVENT_INTERVAL = int(os.getenv("MIN_EVENT_INTERVAL", "60"))

# Monitored thresholds (env → list)
raw = os.getenv("FEE_THRESHOLDS", "1,2,3,5,8,12,20,35,60,100,200")
THRESHOLDS = sorted({float(x) for x in raw.split(",") if x.strip()})

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


# ───────────────────────── helpers ─────────────────────────
def fetch_gas_oracle() -> dict:
    url = "https://api.etherscan.io/api"
    params = {"module": "gastracker", "action": "gasoracle", "apikey": ETHERSCAN_API_KEY}
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    if data.get("status") != "1":
        raise RuntimeError(f"Etherscan error: {data.get('message')}")
    return data["result"]


def detect_cross(prev_fee: float, curr_fee: float):
    down = [t for t in THRESHOLDS if prev_fee >= t > curr_fee]
    up   = [t for t in THRESHOLDS if prev_fee <= t < curr_fee]
    if down:
        return {"threshold": max(down), "state": "below"}
    if up:
        return {"threshold": min(up), "state": "above"}
    return None


def fmt_gwei(val: float) -> str:
    """Trim decimals based on magnitude."""
    if val >= 10:
        return f"{val:.1f}"
    if val >= 1:
        return f"{val:.2f}"
    if val >= 0.1:
        return f"{val:.3f}"
    return f"{val:.4f}"


# ───────────────────────── main job ─────────────────────────
def fetch_and_cache_gas():
    try:
        result   = fetch_gas_oracle()
        curr_fee = float(result.get("suggestBaseFee", 0.0))
        block    = result["LastBlock"]

        prev_fee = float(r.get(LAST_FEE_KEY) or curr_fee)
        event    = detect_cross(prev_fee, curr_fee)

        # ─── debounce ───
        now_ts   = time.time()
        last_ts  = float(r.get(LAST_EVENT_TS_KEY) or 0)
        allow_push = (now_ts - last_ts) >= MIN_EVENT_INTERVAL
        # ─────────────────

        if event:
            t_key = str(event["threshold"])
            r.hset(THRESHOLD_KEY, t_key, event["state"])
            r.hset(THRESHOLD_TS_KEY, t_key, datetime.utcnow().isoformat())

            if allow_push:
                arrow = "▼" if event["state"] == "below" else "▲"
                delta = curr_fee - prev_fee
                safe  = fmt_gwei(float(result["SafeGasPrice"]))
                prop  = fmt_gwei(float(result["ProposeGasPrice"]))
                fast  = fmt_gwei(float(result["FastGasPrice"]))
                utc_ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

                tg_msg = (
                    f"⛽️ {arrow} *Gas {event['state']} {t_key} Gwei*\n"
                    f"`Now:`  {fmt_gwei(curr_fee)} Gwei   (Δ {delta:+.2f})\n"
                    f"`Safe / Prop / Fast:` {safe} / {prop} / {fast} Gwei\n"
                    f"[Block {block}](https://etherscan.io/block/{block}) · {utc_ts}"
                )

                print(f"[EVENT] {tg_msg.replace('*', '').replace('`', '')}")
                send_message(tg_msg)
                r.set(LAST_EVENT_TS_KEY, now_ts)
            else:
                gap = now_ts - last_ts
                print(f"[SKIP] Debounce: {gap:.1f}s < {MIN_EVENT_INTERVAL}s")

        # persist latest fee
        r.set(LAST_FEE_KEY, curr_fee)

        # cache oracle snapshot
        gas_data = {
            "safe":         f"{result['SafeGasPrice']} Gwei",
            "propose":      f"{result['ProposeGasPrice']} Gwei",
            "fast":         f"{result['FastGasPrice']} Gwei",
            "base_fee":     f"{curr_fee:.6f} Gwei",
            "last_block":   block,
            "last_updated": datetime.utcnow().isoformat(),
        }
        r.set(GAS_KEY, json.dumps(gas_data))

        print(
            f"[INFO] Gas updated @ block {block} → base_fee={curr_fee:.6f} Gwei "
            f"(prev={prev_fee:.6f})"
        )

    except Exception as exc:
        print(f"[ERROR] fetch_and_cache_gas: {exc}")


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_and_cache_gas, "interval", seconds=10, max_instances=1)
    scheduler.start()
