import os, time, json, requests
from typing import List, Dict

def _endpoint_for_appid(app_id: str) -> str:
    # If your key looks sandbox'y, use sandbox endpoint automatically
    if ("-SBX-" in app_id) or app_id.upper().startswith("SBX-"):
        return "https://svcs.sandbox.ebay.com/services/search/FindingService/v1"
    return "https://svcs.ebay.com/services/search/FindingService/v1"

def search_ebay(keyword: str, per_page: int = 12) -> List[Dict]:
    app_id = os.environ.get("EBAY_APP_ID")
    if not app_id:
        raise RuntimeError("EBAY_APP_ID not set")

    endpoint = _endpoint_for_appid(app_id)

    # Keep filters loose at first so we actually get items back
    params = {
        "OPERATION-NAME": "findItemsByKeywords",
        "SERVICE-VERSION": "1.13.0",
        "SECURITY-APPNAME": app_id,                # required
        "GLOBAL-ID": "EBAY-US",
        "RESPONSE-DATA-FORMAT": "JSON",
        "REST-PAYLOAD": "",
        "keywords": keyword,
        "paginationInput.entriesPerPage": str(per_page),
        "sortOrder": "BestMatch",
        # NOTE: removed strict ListingType filter for now
        # "itemFilter(0).name": "ListingType",
        # "itemFilter(0).value(0)": "FixedPrice"
    }
    headers = {
        "User-Agent": "TrendDropBot/1.0",
        # Some proxies care about the SOA header too—add it just in case:
        "X-EBAY-SOA-SECURITY-APPNAME": app_id
    }

    try:
        r = requests.get(endpoint, params=params, headers=headers, timeout=25)
        status = r.status_code
        if status != 200:
            print(f"[ebay] HTTP {status} for '{keyword}' -> {r.text[:300]}")
            return []
        data = r.json()
    except Exception as e:
        print(f"[ebay] request failed for '{keyword}': {e}")
        return []

    try:
        items = (data.get("findItemsByKeywordsResponse", [{}])[0]
                    .get("searchResult", [{}])[0]
                    .get("item", []))
    except Exception as e:
        print(f"[ebay] parse failed for '{keyword}': {e}\n{json.dumps(data)[:500]}")
        items = []

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
            # keep going if one item is malformed
            print(f"[ebay] item parse error for '{keyword}': {e}")
            continue

    print(f"[ebay] '{keyword}' -> {len(out)} items (endpoint={endpoint})")
    return out
