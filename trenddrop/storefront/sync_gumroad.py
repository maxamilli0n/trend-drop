# TD-AUTO: BEGIN storefront-sync-gumroad
from __future__ import annotations
import os
from pathlib import Path


def _get(key: str) -> str | None:
    v = os.environ.get(key)
    return v.strip() if v else None


def main() -> int:
    token = _get("GUMROAD_ACCESS_TOKEN")
    product = _get("GUMROAD_PRODUCT_ID")
    if not token or not product:
        print("[sync_gumroad] missing GUMROAD_*; skipping")
        return 0

    out = Path("out")
    pdf = out / "weekly-report.pdf"
    csv = out / "weekly-report.csv"
    if not pdf.exists() and not csv.exists():
        print("[sync_gumroad] no artifacts; skipping")
        return 0

    # Best-effort: update product content/fields with latest URLs via report-links
    signed_urls: dict[str, str] = {}
    try:
        import requests
        supa = _get("SUPABASE_URL")
        svc = _get("SUPABASE_SERVICE_ROLE_KEY")
        if supa and svc:
            for fmt in ("pdf", "csv"):
                r = requests.post(
                    f"{supa}/functions/v1/report-links",
                    headers={"authorization": f"Bearer {svc}"},
                    json={"mode": "weekly", "format": fmt},
                    timeout=20,
                )
                if r.ok:
                    signed_urls[fmt] = r.json().get("url") or ""

        # Gumroad product update (metadata-like via custom fields description)
        desc = "TrendDrop Weekly Pack — latest links in fields."
        fields = []
        if signed_urls.get("pdf"):
            fields.append({"name": "latest_pdf", "value": signed_urls["pdf"]})
        if signed_urls.get("csv"):
            fields.append({"name": "latest_csv", "value": signed_urls["csv"]})

        payload = {"product_id": product, "description": desc}
        # Gumroad API is limited; many edits require dashboard; we best-effort store links
        r2 = requests.post(
            "https://api.gumroad.com/v2/products/" + product,
            data=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        if not r2.ok:
            print(f"[sync_gumroad] update failed: {r2.status_code} {r2.text}")
    except Exception as e:
        print(f"[sync_gumroad] request failed: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# TD-AUTO: END storefront-sync-gumroad


