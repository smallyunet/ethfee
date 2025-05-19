# services/telegram.py
"""
Light-weight Telegram notifier.
Import and call send_message("text") whenever you need.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID   = os.getenv("TG_CHAT_ID")      # "@channel" or "-100..."

def send_message(text: str, markdown: bool = True) -> None:
    """
    Send a message to Telegram channel.
    Silently no-ops if TG_BOT_TOKEN or TG_CHAT_ID is missing.
    """
    if not (TG_BOT_TOKEN and TG_CHAT_ID):
        return

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown" if markdown else None,
        "disable_web_page_preview": True,
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as exc:
        # Do NOT raise — callers不想因为 TG 挂掉就崩溃
        print(f"[WARN] Telegram push failed: {exc}")
