# TD-AUTO: BEGIN content-scheduler
from __future__ import annotations
import subprocess


def main() -> int:
    # Placeholder that could schedule posting; here we simply run both steps.
    try:
        subprocess.run(["python", "-m", "trenddrop.content.generate_captions"], check=False)
        subprocess.run(["python", "-m", "trenddrop.content.post_twitter"], check=False)
    except Exception as e:
        print(f"[scheduler] failed: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# TD-AUTO: END content-scheduler


