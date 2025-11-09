import os, time
from pathlib import Path
from trenddrop.utils.env_loader import load_env_once
from typing import List, Dict

# Load environment variables only from root .env
ENV_PATH = load_env_once()
from utils.trends import top_topics
from utils.sources import search_ebay
from utils.epn import affiliate_wrap
from utils.publish import update_storefront, post_telegram

def _get_int_env(name: str, default: int) -> int:
    try:
        value_str = os.environ.get(name)
        if value_str is None or value_str == "":
            return default
        value = int(value_str)
        return value if value >= 0 else default
    except Exception:
        return default

def _get_float_env(name: str, default: float) -> float:
    try:
        value_str = os.environ.get(name)
        if value_str is None or value_str == "":
            return default
        value = float(value_str)
        return value if value >= 0 else default
    except Exception:
        return default

def _get_float_env_between(name: str, default: float, min_value: float, max_value: float) -> float:
    val = _get_float_env(name, default)
    if val < min_value:
        return min_value
    if val > max_value:
        return max_value
    return val

def score(p: Dict) -> float:
    base = 0.0
    base += (p.get("top_rated", False) * 5)
    base += min(p.get("seller_feedback", 0)/1000, 5)
    price = p.get("price", 0.0)
    if price > 0:
        if 15 <= price <= 150: base += 4
        elif 5 <= price < 15: base += 2
        elif 150 < price <= 400: base += 1
    return base

def dedupe(products: List[Dict]) -> List[Dict]:
    seen, out = set(), []
    for p in products:
        key = p.get("url")
        if key and key not in seen:
            seen.add(key); out.append(p)
    return out

def main():
    topics_limit = _get_int_env("TREND_TOPICS_LIMIT", 1)
    per_page = _get_int_env("TREND_PER_PAGE", 5)
    sleep_secs = _get_float_env("TREND_SLEEP_SECS", 5.0)
    sleep_jitter = _get_float_env_between("TREND_SLEEP_JITTER", 0.0, 0.0, 10.0)
    picks_limit = _get_int_env("TREND_PICKS_LIMIT", 5)
    telegram_limit = _get_int_env("TREND_TELEGRAM_LIMIT", 5)

    topics = top_topics(limit=topics_limit)
    print(f"[bot] topics: {topics}")
    candidates: List[Dict] = []
    for i, t in enumerate(topics):
        try:
            found = search_ebay(t, per_page=per_page)
            print(f"[bot] found {len(found)} for topic '{t}'")
            for item in found:
                item["score"] = score(item)
                item["tags"] = [t]
                item["url"] = affiliate_wrap(item["url"], custom_id=t.replace(" ", "_")[:40])
            candidates += found
        except Exception as e:
            print(f"[bot] WARN search failed '{t}': {e}")
        # optional jitter to desynchronize bursts
        if sleep_secs > 0:
            jitter = 0.0
            try:
                import random
                jitter = random.uniform(0.0, sleep_jitter) if sleep_jitter > 0 else 0.0
            except Exception:
                jitter = 0.0
            time.sleep(sleep_secs + jitter)  # configurable pause between calls

    candidates = dedupe(candidates)
    picks = sorted(candidates, key=lambda x: x.get("score", 0.0), reverse=True)[:picks_limit]
    print(f"[bot] candidates={len(candidates)} picks={len(picks)}")
    update_storefront(picks)
    post_telegram(picks, limit=telegram_limit)
    print(f"[bot] posted {len(picks)} items from {len(topics)} topics")
    
if __name__ == "__main__":
    main()
