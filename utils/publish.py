import os, json, time, requests, pathlib, html
from typing import List, Dict
from utils.db import save_run_summary, upsert_products
from utils.ai import caption_for

DOCS_DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "data")
PRODUCTS_PATH = os.path.join(DOCS_DATA, "products.json")

def ensure_dirs():
    pathlib.Path(DOCS_DATA).mkdir(parents=True, exist_ok=True)

def update_storefront(products: List[Dict]):
    # enrich captions for site/telegram
    for p in products:
        try:
            p["caption"] = caption_for(p)
        except Exception:
            p["caption"] = p.get("title", "")
    ensure_dirs()
    with open(PRODUCTS_PATH, "w", encoding="utf-8") as f:
        json.dump({"updated_at": int(time.time()), "products": products}, f, indent=2)
    # also persist to Supabase if configured
    try:
        upsert_products(products)
    except Exception:
        pass

def post_telegram(products: List[Dict], limit=5):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id or not products:
        return

    api = f"https://api.telegram.org/bot{token}"
    pick = products[:limit]
    for p in pick:
        try:
            title = html.escape(str(p.get("title", "")))
            price = p.get("price")
            currency = p.get("currency", "USD")
            url = p.get("url", "")
            img = p.get("image_url")
            caption_extra = p.get("caption") or ""
            price_text = f"{currency} {price:.2f}" if isinstance(price, (int, float)) else f"{currency} {price}"
            caption = f"✅ <b>{title}</b> — {price_text}\n{html.escape(caption_extra)}\n<a href=\"{url}\">View</a>"

            if img:
                requests.post(
                    f"{api}/sendPhoto",
                    data={
                        "chat_id": chat_id,
                        "photo": img,
                        "caption": caption,
                        "parse_mode": "HTML",
                    },
                    timeout=20,
                )
            else:
                requests.post(
                    f"{api}/sendMessage",
                    data={
                        "chat_id": chat_id,
                        "text": caption,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    },
                    timeout=20,
                )
            time.sleep(0.4)
        except Exception:
            # best-effort; continue with next product
            continue

    # after posting, log a run summary
    try:
        uniq_topics = set()
        for p in products:
            for t in p.get("tags", []) or []:
                uniq_topics.add(t)
        save_run_summary(topic_count=len(uniq_topics) or 1, item_count=len(pick))
    except Exception:
        pass
