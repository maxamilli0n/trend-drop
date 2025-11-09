# TD-AUTO: BEGIN sync-secrets
from __future__ import annotations
import os
import shlex
import subprocess


KEYS = [
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "PAYHIP_API_KEY",
    "PAYHIP_PRODUCT_ID",
    "GUMROAD_ACCESS_TOKEN",
    "GUMROAD_PRODUCT_ID",
    "PLAUSIBLE_DOMAIN",
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
]


def main() -> int:
    supa_url = os.environ.get("SUPABASE_URL")
    if not supa_url:
        print("[sync_secrets] SUPABASE_URL not set; skipping")
        return 0
    env_pairs = []
    for k in KEYS:
        v = os.environ.get(k)
        if v:
            env_pairs.append((k, v))
    if not env_pairs:
        print("[sync_secrets] no new keys present; skipping")
        return 0
    # Best-effort: supabase CLI expected to be installed in CI environment
    try:
        args = ["supabase", "secrets", "set"] + [f"{k}={v}" for k, v in env_pairs]
        print("[sync_secrets] ", " ".join(shlex.quote(a) for a in args[:-1]), "…")
        subprocess.run(args, check=False)
    except Exception as e:
        print(f"[sync_secrets] failed: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# TD-AUTO: END sync-secrets


