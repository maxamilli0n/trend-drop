import os, time
from typing import List, Dict, Optional

try:
    from supabase import create_client, Client
except Exception:
    create_client = None  # type: ignore
    Client = object  # type: ignore

_SB_URL = os.environ.get("SUPABASE_URL")
_SB_KEY = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
_sb: Optional[Client] = create_client(_SB_URL, _SB_KEY) if (create_client and _SB_URL and _SB_KEY) else None


def sb() -> Optional[Client]:
    return _sb


def save_run_summary(topic_count: int, item_count: int) -> Optional[str]:
    if not _sb:
        return None
    now = int(time.time())
    try:
        r = _sb.table("runs").insert({"ran_at": now, "topics": topic_count, "items": item_count}).execute()
        return str((r.data or [{}])[0].get("id"))
    except Exception:
        return None


def upsert_products(products: List[Dict]):
    if not _sb or not products:
        return
    rows = []
    for p in products:
        title = p.get("title")
        url = p.get("url")
        if not title or not url:
            continue
        rows.append({
            "source": p.get("source", "ebay"),
            "title": title,
            "price": p.get("price"),
            "currency": p.get("currency", "USD"),
            "image_url": p.get("image_url"),
            "url": url,
            "keyword": p.get("keyword"),
            "seller_feedback": p.get("seller_feedback"),
            "top_rated": p.get("top_rated", False),
        })
    if rows:
        try:
            _sb.table("products").upsert(rows, on_conflict="url").execute()
        except Exception:
            pass


