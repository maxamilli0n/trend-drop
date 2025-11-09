# TD-AUTO: BEGIN storefront-sync-stripe
from __future__ import annotations
import os
import sys
import json
from pathlib import Path
from typing import Optional


def _get(key: str) -> Optional[str]:
    v = os.environ.get(key)
    return v.strip() if v else None


def _read(path: Path) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def main() -> int:
    # Graceful no-op if missing secrets
    secret = _get("STRIPE_SECRET_KEY")
    product_id = _get("STRIPE_PRODUCT_ID")
    reports_bucket = _get("REPORTS_BUCKET") or "trenddrop-reports"
    if not secret or not product_id:
        print("[sync_stripe] missing STRIPE_* secrets; skipping")
        return 0

    # Only use existing outputs; do not generate
    out = Path("out")
    pdf = out / "weekly-report.pdf"
    csv = out / "weekly-report.csv"
    if not pdf.exists() and not csv.exists():
        print("[sync_stripe] no artifacts found; skipping")
        return 0

    # Prepare metadata update (description + links)
    description = "TrendDrop Weekly Pack — latest PDF + CSV"
    files: list[tuple[str, Path]] = []
    if pdf.exists():
        files.append(("pdf", pdf))
    if csv.exists():
        files.append(("csv", csv))

    # Best-effort signed URL retrieval via report-links function if configured
    signed_urls: dict[str, str] = {}
    try:
        supa_url = _get("SUPABASE_URL")
        svc = _get("SUPABASE_SERVICE_ROLE_KEY")
        if supa_url and svc:
            import requests
            for fmt, _p in files:
                r = requests.post(
                    f"{supa_url}/functions/v1/report-links",
                    headers={"authorization": f"Bearer {svc}", "content-type": "application/json"},
                    json={"mode": "weekly", "format": fmt},
                    timeout=20,
                )
                if r.ok:
                    signed_urls[fmt] = r.json().get("url") or ""
    except Exception as e:
        print(f"[sync_stripe] signed URL fetch failed: {e}")

    # Update Stripe product metadata (no upload of files; point to storage URLs)
    try:
        import requests
        meta = {f"latest_{k}_url": v for k, v in signed_urls.items() if v}
        data = {"metadata": meta, "description": description}
        r = requests.post(
            f"https://api.stripe.com/v1/products/{product_id}",
            data=data,
            headers={"Authorization": f"Bearer {secret}"},
            timeout=20,
        )
        if not r.ok:
            print(f"[sync_stripe] stripe update failed: {r.status_code} {r.text}")
    except Exception as e:
        print(f"[sync_stripe] stripe request failed: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# TD-AUTO: END storefront-sync-stripe


