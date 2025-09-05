from urllib.parse import quote
import os

def affiliate_wrap(raw_url: str, custom_id: str = "") -> str:
    camp = os.environ.get("EPN_CAMPAIGN_ID")
    if not camp:
        return raw_url
    cid_prefix = os.environ.get("CUSTOM_ID_PREFIX", "trenddrop")
    custom = f"{cid_prefix}_{custom_id}" if custom_id else cid_prefix
    return f"https://rover.ebay.com/rover/1/711-53200-19255-0/1?campid={camp}&customid={quote(custom)}&toolid=10001&mpre={quote(raw_url, safe='')}"
