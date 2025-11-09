import json
import os
import sys
import time
from pathlib import Path

import requests
from pathlib import Path
from trenddrop.utils.env_loader import load_env_once

# Load .env only from project root (one level up from package root if run within repo)
ENV_PATH = load_env_once()


def _env(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        raise SystemExit(f"Missing required env: {name}")
    return v


def main() -> None:
    # Show which .env file was resolved and confirm key presence
    print("Loaded .env from:", ENV_PATH)
    print("Supabase URL:", os.getenv("SUPABASE_URL"))
    print(
        "[smoke] Keys present → URL:%s ANON:%s SRV:%s"
        % (
            bool(os.environ.get("SUPABASE_URL")),
            bool(os.environ.get("SUPABASE_ANON_KEY")),
            bool(os.environ.get("SUPABASE_SERVICE_ROLE_KEY")),
        )
    )

    # Ensure keys exist so public URL generation works correctly
    _env("SUPABASE_URL")
    _env("SUPABASE_ANON_KEY")

    manifest_path = Path("out") / "artifacts.json"
    if not manifest_path.exists():
        raise SystemExit("artifacts.json missing; run the generator before smoke_test")

    manifest = json.loads(manifest_path.read_text("utf-8"))
    arts = manifest.get("artifacts") or {}
    pdf_url = arts.get("pdf_url_latest") or arts.get("pdf_url_dated")
    csv_url = arts.get("csv_url_latest") or arts.get("csv_url_dated")

    if not pdf_url:
        raise SystemExit("No PDF URL found in artifacts.json")

    def _assert_url(url: str) -> None:
        try:
            r = requests.get(url, timeout=30)
        except Exception as e:
            raise SystemExit(f"Request failed for {url}: {e}")
        if r.status_code != 200:
            raise SystemExit(f"Non-200 for {url}: {r.status_code}")
        if len(r.content) <= 5000:
            raise SystemExit(f"File too small for {url}: {len(r.content)} bytes")

    _assert_url(pdf_url)
    if csv_url:
        _assert_url(csv_url)

    print("✅ Smoke test passed")


if __name__ == "__main__":
    main()


