import os
from typing import List, Dict
from utils.trends import top_topics
from utils.sources import search_ebay
from utils.epn import affiliate_wrap
from utils.publish import update_storefront, post_telegram

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
    topics = top_topics(limit=8)
    print(f"[bot] topics: {topics}")
    candidates: List[Dict] = []
    for t in topics:
        try:
            found = search_ebay(t, per_page=12)
            print(f"[bot] found {len(found)} for topic '{t}'")
            for item in found:
                item["score"] = score(item)
                item["tags"] = [t]
                item["url"] = affiliate_wrap(item["url"], custom_id=t.replace(" ", "_")[:40])
            candidates += found
        except Exception as e:
            print(f"[bot] WARN search failed '{t}': {e}")
            continue
    candidates = dedupe(candidates)
    picks = sorted(candidates, key=lambda x: x.get("score", 0.0), reverse=True)[:12]
    print(f"[bot] candidates={len(candidates)} picks={len(picks)}")
    update_storefront(picks)
    post_telegram(picks[:6])
    print(f"[bot] posted {len(picks)} items from {len(topics)} topics")
    
if __name__ == "__main__":
    main()
