import os, json, time, requests, pathlib

DOCS_DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "data")
PRODUCTS_PATH = os.path.join(DOCS_DATA, "products.json")

def ensure_dirs():
    pathlib.Path(DOCS_DATA).mkdir(parents=True, exist_ok=True)

def update_storefront(products):
    ensure_dirs()
    with open(PRODUCTS_PATH, "w", encoding="utf-8") as f:
        json.dump({"updated_at": int(time.time()), "products": products}, f, indent=2)

def post_telegram(products, limit=5):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    pick = products[:limit]
    lines = []
    for p in pick:
        lines.append(f"✅ <b>{p['title']}</b> — {p['currency']} {p['price']:.2f}\n<a href='{p['url']}'>View</a>")
    msg = "\n\n".join(lines)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": False}, timeout=15)
    except Exception:
        pass
