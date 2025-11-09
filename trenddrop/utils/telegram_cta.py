# -*- coding: utf-8 -*-
import os
import time
import json
import requests
from pathlib import Path
from pathlib import Path as _Path
from trenddrop.utils.env_loader import load_env_once

# Ensure root .env is loaded even when running from subfolders
ENV_PATH = load_env_once()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
CTA_URL = os.getenv("GUMROAD_CTA_URL", "").strip()
CTA_BATCH_SIZE = int(os.getenv("CTA_BATCH_SIZE", "5"))
CTA_COOLDOWN_HOURS = float(os.getenv("CTA_COOLDOWN_HOURS", "6"))

STATE_DIR = Path(".state")
STATE_DIR.mkdir(exist_ok=True)
STATE_FILE = STATE_DIR / "last_cta.json"


def _tg_send(text: str, disable_preview: bool = False):
    if not (BOT_TOKEN and CHAT_ID):
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": disable_preview}
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


def record_product_posted_count():
    """Increment a simple counter of how many product messages were sent in this run."""
    cnt_file = STATE_DIR / "batch_counter.json"
    data = {"count": 0}
    if cnt_file.exists():
        try:
            data = json.loads(cnt_file.read_text("utf-8"))
        except Exception:
            pass
    data["count"] = data.get("count", 0) + 1
    cnt_file.write_text(json.dumps(data), encoding="utf-8")
    return data["count"]


def reset_product_posted_count():
    (STATE_DIR / "batch_counter.json").write_text(json.dumps({"count": 0}), encoding="utf-8")


def _cooldown_ok() -> bool:
    """Return True if cooldown period has elapsed since last CTA."""
    now = time.time()
    if not STATE_FILE.exists():
        return True
    try:
        last = json.loads(STATE_FILE.read_text("utf-8")).get("ts", 0.0)
    except Exception:
        last = 0.0
    return (now - last) >= (CTA_COOLDOWN_HOURS * 3600)


def _stamp_now():
    STATE_FILE.write_text(json.dumps({"ts": time.time()}), encoding="utf-8")


def maybe_send_cta():
    """
    Call this after each product message.
    When the batch size is reached AND cooldown allows, send the CTA and reset the batch counter.
    """
    if not CTA_URL:
        return  # no CTA configured
    current = record_product_posted_count()
    if current < CTA_BATCH_SIZE:
        return
    # reached batch size:
    reset_product_posted_count()
    if not _cooldown_ok():
        return
    _tg_send(f"📊 Full Weekly Report → {CTA_URL}", disable_preview=False)
    _stamp_now()


