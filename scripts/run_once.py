import os
import requests
from pathlib import Path
from trenddrop.utils.env_loader import load_env_once
from trenddrop.telegram_utils import send_text
from trenddrop.config import gumroad_cta_url

ENV_PATH = load_env_once()

CAMPID = os.getenv("EPN_CAMPAIGN_ID", "").strip()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def epn_link(raw_url: str, campid: str) -> str:
    if not campid:
        return raw_url
    sep = '&' if '?' in raw_url else '?'
    return f"{raw_url}{sep}campid={campid}"


def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False,
    }
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    # TODO: paste your real ebay product url between quotes:
    test_product_url = "https://www.ebay.com/itm/315402417803?_trkparms=amclksrc%3DITM%26aid%3D1110013%26algo%3DHOMESPLICE.SIMRXI%26ao%3D1%26asc%3D20250416171351%26meid%3Dacc1c124c5104888aee93040780ba2c8%26pid%3D102672%26rk%3D3%26rkt%3D20%26mehot%3Dpp%26itm%3D315402417803%26pmt%3D0%26noa%3D1%26pg%3D4375194%26algv%3DOrganicPersonalizedRecoSearchEchoWithVDB%26tu%3D01K6E8SVT1PJZGRE2E56S5C0CC"

    if not all([BOT_TOKEN, CHAT_ID]):
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env")

    affiliate_url = epn_link(test_product_url, CAMPID)
    base_post_text = f"Test Product\n{affiliate_url}"
    cta = (
        "\n\n\ud83d\udce6 <b>Full Weekly Report \u2192</b> "
        f"{gumroad_cta_url()}\n"
        "\ud83d\udd0e <i>Top 50 trending eBay products (PDF + CSV)</i>"
    )
    message = base_post_text + cta

    print("Posting to Telegram...")
    send_text(message, parse_mode="HTML", disable_web_page_preview=False)
    print("\u2705 Posted: True")
    print("Now open Telegram, tap the link, and that click should appear in EPN soon.")


