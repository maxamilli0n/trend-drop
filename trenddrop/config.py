import os
from pathlib import Path
from trenddrop.utils.env_loader import load_env_once

ENV_PATH = load_env_once()
from datetime import datetime


def env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name, default)
    if v is None:
        return None
    v = v.strip()
    return v or default


BOT_TOKEN = env("TELEGRAM_BOT_TOKEN")
CHAT_ID = env("TELEGRAM_CHAT_ID")                # DM / test chat
CHANNEL_ID = env("TELEGRAM_CHANNEL_ID")          # @TrendDropStudio or numeric


def tg_targets() -> list[str]:
    targets: list[str] = []
    if CHAT_ID:
        targets.append(CHAT_ID)
    if CHANNEL_ID:
        targets.append(CHANNEL_ID)
    # de-dupe just in case
    return list(dict.fromkeys(targets))


def gumroad_cta_url() -> str:
    raw = env("GUMROAD_CTA_URL", "")
    if not raw:
        return ""
    # allow {date} token
    return raw.replace("{date}", datetime.utcnow().strftime("%Y-%m-%d"))


