import os
import pathlib
from pathlib import Path
import time
from typing import List, Dict, Tuple
import re
from urllib.parse import urlparse, urlunparse

from utils.report import (
    generate_weekly_pdf,
    generate_table_pdf,
    write_csv,
)
from trenddrop.utils.supabase_upload import upload_file
from trenddrop.utils.env_loader import load_env_once
from utils.db import sb
ENV_PATH = load_env_once()


def _ensure_dir(path: str) -> None:
    p = pathlib.Path(path)
    p.mkdir(parents=True, exist_ok=True)


def _get_env(name: str, default: str | None = None) -> str | None:
    val = os.environ.get(name)
    return val if val not in (None, "") else default


def _get_int(name: str, default: int) -> int:
    try:
        v = os.environ.get(name)
        return int(v) if v not in (None, "") else default
    except Exception:
        return default


def _load_products_from_supabase(limit: int) -> List[Dict]:
    client = sb()
    if not client:
        return []
    try:
        # Pull recent products to pick from (include seller feedback & top_rated)
        prod = client.table("products").select(
            "title, price, currency, image_url, url, seller_feedback, top_rated"
        ).limit(500).execute()
        products = list(prod.data or [])
        # Click counts last 7 days via SQL RPC if available
        try:
            clicks = client.rpc("exec", {"sql": "select product_url as url, count(*) as c from clicks where clicked_at >= now() - interval '7 days' group by product_url"}).execute()
            by_url = {row.get("url"): int(row.get("c") or 0) for row in (clicks.data or [])}
            for p in products:
                u = p.get("url")
                if u in by_url:
                    p["signals"] = by_url[u]
        except Exception:
            pass
        return products[:limit]
    except Exception:
        return []


def _load_products_from_docs(limit: int) -> List[Dict]:
    import json
    try:
        root = pathlib.Path(__file__).resolve().parents[2]
        with open(root / "docs" / "data" / "products.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            items = data.get("products", []) or []
            return items[:limit]
    except Exception:
        return []


def main() -> None:
    # Load .env if present so local runs have credentials
    # .env already loaded above
    # Mode and options
    mode = _get_env("REPORT_MODE", "weekly_paid")
    max_items = _get_int("REPORT_MAX_ITEMS", 50)
    title = _get_env("REPORT_TITLE", "TrendDrop Report")

    out_dir = pathlib.Path("out")
    _ensure_dir(str(out_dir))

    ts = time.strftime("%Y-%m-%d", time.gmtime())
    is_weekly = "weekly" in (mode or "")
    pdf_outfile = out_dir / ("weekly-report.pdf" if is_weekly else "daily-report.pdf")
    csv_outfile = out_dir / ("weekly-report.csv" if is_weekly else "daily-report.csv")

    # Source products (over-fetch, then dedupe)
    products = _load_products_from_supabase(limit=max_items * 3) or _load_products_from_docs(limit=max_items * 3)

    # ---- Robust dedupe (normalize URL; fallback title+price); prefer higher seller_feedback ----
    def _normalize_url(u: str | None) -> str:
        if not u:
            return ""
        p = urlparse(u)
        clean = p._replace(query="", fragment="")
        netloc = (p.hostname or "").lower()
        if p.port:
            netloc = f"{netloc}:{p.port}"
        clean = clean._replace(netloc=netloc)
        return urlunparse(clean)

    def _normalize_title(t: str | None) -> str:
        if not t:
            return ""
        t = t.lower()
        t = re.sub(r"\s+", " ", t)
        t = re.sub(r"[^\w\s]+", "", t)
        return t.strip()

    def _dedupe(items: List[Dict], prefer_key: str = "seller_feedback") -> List[Dict]:
        seen: Dict[Tuple[str, str], Dict] = {}
        order: List[Tuple[str, str]] = []
        def choose(old: Dict, new: Dict) -> Dict:
            try:
                ov = int(old.get(prefer_key, 0) or 0)
                nv = int(new.get(prefer_key, 0) or 0)
                return new if nv > ov else old
            except Exception:
                return old
        for r in items:
            key_url = _normalize_url(r.get("url"))
            if key_url:
                key = ("url", key_url)
            else:
                key = ("title_price", f"{_normalize_title(r.get('title'))}|{r.get('price')}")
            if key not in seen:
                seen[key] = r
                order.append(key)
            else:
                seen[key] = choose(seen[key], r)
        return [seen[k] for k in order]

    def _score_balanced(p: Dict) -> float:
        score = 0.0
        # Top rated sellers get a boost
        if p.get("top_rated"):
            score += 5.0
        # Normalize feedback roughly to 0..5
        try:
            score += min(float(p.get("seller_feedback") or 0) / 1000.0, 5.0)
        except Exception:
            pass
        # Favor prices in mid-range
        price = p.get("price")
        try:
            price = float(price)
            if 15 <= price <= 150:
                score += 4.0
            elif 5 <= price < 15:
                score += 2.0
            elif 150 < price <= 400:
                score += 1.0
        except Exception:
            pass
        # Optional signals field if available
        try:
            sig = float(p.get("signals") or 0)
            score += min(sig / 1000.0, 5.0)
        except Exception:
            pass
        return score

    def _sort_items(items: List[Dict], strategy: str) -> List[Dict]:
        if strategy == "seller_feedback":
            return sorted(items, key=lambda x: x.get("seller_feedback") or 0, reverse=True)
        if strategy == "signals":
            return sorted(items, key=lambda x: x.get("signals") or 0, reverse=True)
        if strategy == "price_low":
            return sorted(items, key=lambda x: (x.get("price") or 0))
        if strategy == "price_high":
            return sorted(items, key=lambda x: (x.get("price") or 0), reverse=True)
        # balanced
        return sorted(items, key=_score_balanced, reverse=True)

    products = _dedupe(products)
    strategy = _get_env("REPORT_SORT_STRATEGY", "balanced") or "balanced"
    products = _sort_items(products, strategy)[:max_items]
    if not products:
        print("[reports] no products found; exiting")
        return

    # Layout selection
    layout = _get_env("REPORT_LAYOUT", "table")
    if layout == "table":
        # Dynamic columns via env or default set
        import json
        default_cols = [
            {"key": "title", "label": "Title"},
            {"key": "price", "label": "Price"},
            {"key": "currency", "label": "Currency"},
            {"key": "seller_feedback", "label": "Seller FB"},
            {"key": "signals", "label": "Signals"},
        ]
        cols_json = _get_env("REPORT_COLUMNS")
        try:
            columns = json.loads(cols_json) if cols_json else default_cols
        except Exception:
            columns = default_cols
        print(f"[reports] generating table PDF ({len(products)} items) -> {pdf_outfile}")
        generate_table_pdf(products, str(pdf_outfile), columns, title)
        # CSV alongside
        write_csv(products, str(csv_outfile), columns)
    else:
        print(f"[reports] generating PDF ({len(products)} items) -> {pdf_outfile}")
        generate_weekly_pdf(products, str(pdf_outfile))

    # Optional: upload latest to Supabase Storage
    # Resolve bucket (prefer REPORTS_BUCKET for Phase 2, fallback to legacy SUPABASE_BUCKET)
    bucket = _get_env("REPORTS_BUCKET", None) or _get_env("SUPABASE_BUCKET", "trenddrop-reports")
    latest_pdf_key = "weekly/latest.pdf"
    latest_csv_key = "weekly/latest.csv"
    dated_dir = f"weekly/{ts}"
    dated_pdf_key = f"{dated_dir}/report.pdf"
    dated_csv_key = f"{dated_dir}/report.csv"

    artifacts: Dict[str, str] = {}
    if bucket:
        # Debug: show whether Supabase client is configured
        has_url = bool(os.environ.get("SUPABASE_URL"))
        has_key = bool(os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
        print(f"[reports] supabase configured url={has_url} key={has_key} bucket={bucket}")

        # Upload PDF (latest and dated copy)
        pdf_url_latest = upload_file(bucket, str(pdf_outfile), latest_pdf_key, "application/pdf")
        if pdf_url_latest:
            artifacts["pdf_url_latest"] = pdf_url_latest
            print(f"[reports] uploaded latest PDF: {pdf_url_latest}")
        pdf_url_dated = upload_file(bucket, str(pdf_outfile), dated_pdf_key, "application/pdf")
        if pdf_url_dated:
            artifacts["pdf_url_dated"] = pdf_url_dated
            print(f"[reports] uploaded dated PDF: {pdf_url_dated}")

        # Upload CSV when present (table layout)
        if layout == "table":
            csv_url_latest = upload_file(bucket, str(csv_outfile), latest_csv_key, "text/csv")
            if csv_url_latest:
                artifacts["csv_url_latest"] = csv_url_latest
                print(f"[reports] uploaded latest CSV: {csv_url_latest}")
            csv_url_dated = upload_file(bucket, str(csv_outfile), dated_csv_key, "text/csv")
            if csv_url_dated:
                artifacts["csv_url_dated"] = csv_url_dated
                print(f"[reports] uploaded dated CSV: {csv_url_dated}")

    # Emit artifacts manifest for CI smoke tests
    try:
        import json
        manifest = {
            "bucket": bucket,
            "latest_pdf_key": latest_pdf_key,
            "latest_csv_key": latest_csv_key if layout == "table" else None,
            "dated_pdf_key": dated_pdf_key,
            "dated_csv_key": dated_csv_key if layout == "table" else None,
            "artifacts": artifacts,
        }
        with open(out_dir / "artifacts.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print("[reports] wrote out/artifacts.json")
    except Exception:
        pass


if __name__ == "__main__":
    main()


