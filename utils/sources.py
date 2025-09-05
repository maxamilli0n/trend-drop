import os, requests
from typing import List, Dict

EBAY_FINDING_ENDPOINT = "https://svcs.ebay.com/services/search/FindingService/v1"

def search_ebay(keyword: str, per_page: int = 10) -> List[Dict]:
    app_id = os.environ.get("EBAY_APP_ID")
    if not app_id:
        raise RuntimeError("EBAY_APP_ID not set")
    params = {
        "OPERATION-NAME": "findItemsByKeywords",
        "SERVICE-VERSION": "1.13.0",
        "SECURITY-APPNAME": app_id,
        "RESPONSE-DATA-FORMAT": "JSON",
        "REST-PAYLOAD": "",
        "keywords": keyword,
        "paginationInput.entriesPerPage": str(per_page),
        "sortOrder": "BestMatch",
        "itemFilter(0).name": "ListingType",
        "itemFilter(0).value(0)": "FixedPrice"
    }
    headers = {"User-Agent": "TrendDropBot/1.0"}
    r = requests.get(EBAY_FINDING_ENDPOINT, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()
    items = (data.get("findItemsByKeywordsResponse", [{}])[0]
                .get("searchResult", [{}])[0]
                .get("item", []))
    out = []
    for it in items:
        try:
            price_obj = it.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0]
            price = float(price_obj.get("__value__", 0.0))
            currency = price_obj.get("@currencyId", "USD")
            out.append({
                "source": "ebay",
                "keyword": keyword,
                "title": it.get("title", [""])[0][:160],
                "price": price,
                "currency": currency,
                "image_url": it.get("galleryURL", [""])[0] if it.get("galleryURL") else "",
                "url": it.get("viewItemURL", [""])[0],
                "seller_feedback": int(it.get("sellerInfo", [{}])[0].get("feedbackScore", [0])[0]),
                "top_rated": it.get("topRatedListing", ["false"])[0] == "true"
            })
        except Exception:
            continue
    return out
