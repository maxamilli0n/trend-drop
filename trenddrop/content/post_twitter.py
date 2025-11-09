# TD-AUTO: BEGIN post-twitter
from __future__ import annotations
import os
import json
from pathlib import Path


def _get(k: str) -> str | None:
    v = os.environ.get(k)
    return v.strip() if v else None


def main() -> int:
    api_key = _get("TWITTER_API_KEY")
    api_secret = _get("TWITTER_API_SECRET")
    access_token = _get("TWITTER_API_TOKEN") or _get("TWITTER_ACCESS_TOKEN")
    access_secret = _get("TWITTER_API_TOKEN_SECRET") or _get("TWITTER_ACCESS_TOKEN_SECRET")
    if not (api_key and api_secret and access_token and access_secret):
        print("[post_twitter] missing twitter secrets; skipping")
        return 0

    out = Path("out")
    captions_path = out / "captions.json"
    manifest_path = out / "manifest.json"
    hooks: list[str] = []
    if captions_path.exists():
        hooks = json.loads(captions_path.read_text("utf-8")).get("hooks", [])
    short_url = _get("TRENDLINK_SHORT_URL") or "https://trenddropstudio.github.io/"

    first = (hooks[0] if hooks else "Resell this week’s trends.") + f"\nFull report → {short_url}"
    second = "Earn with your affiliate link."

    try:
        import requests
        # Example using v2 with OAuth 1.0a user context via a proxy or 3rd-party lib.
        # Here we simply log; integrating full OAuth signing is out-of-scope for a stub.
        print("[post_twitter] would post thread:")
        print(first)
        print(second)
    except Exception as e:
        print(f"[post_twitter] failed: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# TD-AUTO: END post-twitter


