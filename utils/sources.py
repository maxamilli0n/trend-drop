import os, time, json, requests
from typing import List, Dict

def _endpoint_for_appid(app_id: str) -> str:
    if ("-SBX-" in app_id) or app_id.upper().startswith("SBX-"):
        return "https://svcs.sandbox.ebay.com/services/search/FindingService/v1"
    return "https://svcs.ebay.com/services/search/FindingService/v1"

def _is_rate_limited(resp_json) -> bool:
    try:
        errs = resp_json["findItemsByKeywordsResponse"][0].get("errorMessage", [{}])[0].get("error", [])
        return any("RateLimiter" in (e.get("subdomain", [""])[0] if isinstance(e.get("subdomain"), list) else "")
                   or "exceeded" in (e.get("message", [""])[0] if isinstance(e.get("message"), list) else "").lower()
                   for e in errs)
    except Exception:
        return False

def search_ebay(keyword: str, per_page: int = 12) -> List[Dict]:
    app_id = os.environ.get("EBAY_APP_ID")
    if not app_id:
        raise RuntimeError("EBAY_APP_ID not set")

    endpoint = _endpoint_for_appid(app_id)
    params = {
        "OPERATION-NAME": "findItemsByKeywords",
        "SERVICE-VERSION": "1.13.0",
        "SECURITY-APPNAME": app_id,
        "GLOBAL-ID": "EBAY-US",
        "RESPONSE-DATA-FORMAT": "JSON",
        "REST-PAYLOAD": "",
        "keywords": keyword,
        "paginationInput.entriesPerPage": str(per_page),
        "sortOrder": "BestMatch",
    }
    headers = {
        "User-Agent": "TrendDropBot/1.0",
        "X-EBAY-SOA-SECURITY-APPNAME": app_id,
        "X-EBAY-SOA-OPERATION-NAME": "findItemsByKeywords",
        "X-EBAY-SOA-GLOBAL-ID": "EBAY-US",
    }

    # retry with exponential backoff on 429/5xx or rate-limit messages
    backoffs = [2, 4, 8]  # seconds
    last_json = None
    for attempt, sleep_s in enumerate([0] + backoffs):
        if sleep_s:
            time.sleep(sleep_s)
        try:
            r = requests.get(endpoint, params=params, headers=headers, timeout=25)
            status = r.status_code
            if status >= 500 or status == 429:
                print(f"[ebay] HTTP {status} for '{keyword}', attempt {attempt+1}/{len(backoffs)+1}")
                continue
            data = r.json()
            last_json = data
            if _is_rate_limited(data):
                print(f"[ebay] Rate-limited for '{keyword}', attempt {attempt+1}/{len(backoffs)+1}")
                continue
            # success path
            items = (data.get("findItemsByKeywordsResponse", [{}])[0]
                        .get("searchResult", [{}])[0]
                        .get("item", []))
            out: List[Dict] = []
            for it in items or []:
                try:
                    title = (it.get("title", [""]) or [""])[0]
                    url = (it.get("viewItemURL", [""]) or [""])[0]
                    gallery = (it.get("galleryURL", [""]) or [""])[0]
                    price_obj = (it.get("sellingStatus", [{}]) or [{}])[0].get("currentPrice", [{}])[0]
                    price = float(price_obj.get("__value__", 0.0))
                    currency = price_obj.get("@currencyId", "USD")
                    top_rated = ((it.get("topRatedListing", ["false"]) or ["false"])[0] == "true")
                    feedback = int((it.get("sellerInfo", [{}]) or [{}])[0].get("feedbackScore", [0])[0])
                    out.append({
                        "source": "ebay",
                        "keyword": keyword,
                        "title": title[:160],
                        "price": price,
                        "currency": currency,
                        "image_url": gallery,
                        "url": url,
                        "seller_feedback": feedback,
                        "top_rated": top_rated
                    })
                except Exception as e:
                    print(f"[ebay] item parse error '{keyword}': {e}")
                    continue
            print(f"[ebay] '{keyword}' -> {len(out)} items (endpoint={endpoint})")
            return out
        except Exception as e:
            print(f"[ebay] request failed '{keyword}': {e}")

    # after retries
    if last_json:
        snippet = json.dumps(last_json)[:400]
        print(f"[ebay] final response snippet for '{keyword}': {snippet}")
    return []
