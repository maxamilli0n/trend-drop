import os, time, json, hashlib, pathlib
from pathlib import Path
from trenddrop.utils.env_loader import load_env_once

# Ensure root .env is loaded
ENV_PATH = load_env_once()
from typing import List, Dict
from utils.ebay_browse import search_browse

def _debug_enabled() -> bool:
    try:
        return str(os.environ.get("DEBUG_EBAY", "")).strip() not in ("", "0", "false", "False")
    except Exception:
        return False

def _endpoint_for_appid(app_id: str) -> str:
    override = os.environ.get("EBAY_FINDING_ENDPOINT")
    if override:
        return override
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

# ---------- Simple file cache & daily budget ----------
_ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
_CACHE_DIR = os.path.join(_ROOT_DIR, ".cache", "ebay")

def _ensure_cache_dir():
    try:
        pathlib.Path(_CACHE_DIR).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

def _cache_enabled() -> bool:
    try:
        ttl_min = float(os.environ.get("EBAY_CACHE_TTL_MIN", 0))
        bypass = str(os.environ.get("EBAY_CACHE_BYPASS", "")).lower() in ("1", "true", "yes")
        return (ttl_min > 0) and (not bypass)
    except Exception:
        return False

def _cache_ttl_secs() -> float:
    try:
        return float(os.environ.get("EBAY_CACHE_TTL_MIN", 0)) * 60.0
    except Exception:
        return 0.0

def _cache_key(keyword: str, per_page: int, global_id: str, request_version: str) -> str:
    raw = f"{keyword}|{per_page}|{global_id}|{request_version}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def _cache_read(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _cache_write(path: str, data) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

def _budget_path() -> str:
    return os.path.join(_CACHE_DIR, "budget.json")

def _load_budget():
    path = _budget_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"date": "", "count": 0}

def _save_budget(data) -> None:
    try:
        with open(_budget_path(), "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

def search_ebay(keyword: str, per_page: int = 12) -> List[Dict]:
    # Prefer Browse API (far better quotas); per_page maps to limit.
    return search_browse(keyword, limit=per_page)
