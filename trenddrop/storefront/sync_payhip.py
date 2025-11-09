# TD-AUTO: BEGIN storefront-sync-payhip
from __future__ import annotations
import os
from pathlib import Path


def _get(key: str) -> str | None:
    v = os.environ.get(key)
    return v.strip() if v else None


def main() -> int:
    api_key = _get("PAYHIP_API_KEY")
    product_id = _get("PAYHIP_PRODUCT_ID")
    if not api_key or not product_id:
        print("[sync_payhip] missing PAYHIP_*; skipping")
        return 0

    out = Path("out")
    pdf = out / "weekly-report.pdf"
    csv = out / "weekly-report.csv"
    if not pdf.exists() and not csv.exists():
        print("[sync_payhip] no artifacts; skipping")
        return 0

    # Best-effort link update (Payhip API is limited; we store description links)
    try:
        import requests
        supa = _get("SUPABASE_URL")
        svc = _get("SUPABASE_SERVICE_ROLE_KEY")
        signed_pdf = signed_csv = None
        if supa and svc:
            r1 = requests.post(f"{supa}/functions/v1/report-links", headers={"authorization": f"Bearer {svc}"}, json={"mode": "weekly", "format": "pdf"}, timeout=20)
            if r1.ok:
                signed_pdf = r1.json().get("url")
            r2 = requests.post(f"{supa}/functions/v1/report-links", headers={"authorization": f"Bearer {svc}"}, json={"mode": "weekly", "format": "csv"}, timeout=20)
            if r2.ok:
                signed_csv = r2.json().get("url")

        desc = "TrendDrop Weekly Pack — latest: "
        if signed_pdf:
            desc += f"\nPDF: {signed_pdf}"
        if signed_csv:
            desc += f"\nCSV: {signed_csv}"

        # Placeholder: Payhip product update endpoint; many actions require dashboard.
        # We attempt a generic PATCH if available in future; for now, no-op with log.
        print(f"[sync_payhip] would update product {product_id} description with links.")
    except Exception as e:
        print(f"[sync_payhip] request failed: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# TD-AUTO: END storefront-sync-payhip


