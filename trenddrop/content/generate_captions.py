# TD-AUTO: BEGIN generate-captions
from __future__ import annotations
import os
import json
from pathlib import Path


TEMPLATE = (
    "Generate 10 short, high-conversion hooks for a weekly product trend report. "
    "Keep each under 90 characters, avoid hashtags, end with a CTA to view the pack."
)


def _get(key: str) -> str | None:
    v = os.environ.get(key)
    return v.strip() if v else None


def main() -> int:
    out = Path("out")
    out.mkdir(exist_ok=True)
    hooks: list[str] = []
    api_key = _get("OPENAI_API_KEY")
    if not api_key:
        # Fallback deterministic hooks
        hooks = [
            "Flip fast: This week’s top resell winners.",
            "Trending now. High demand, low supply.",
            "Stop guessing. Start flipping.",
            "10x better sourcing in 5 minutes.",
            "Snapshots of what’s moving today.",
            "Buy right. Sell faster.",
            "Margin-first picks for this week.",
            "Proven demand. Fresh every week.",
            "Beat the market with the pack.",
            "Skim the top. Profit the gap.",
        ]
    else:
        try:
            import requests
            prompt = TEMPLATE
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a concise marketing copywriter."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                },
                timeout=30,
            )
            if r.ok:
                text = r.json()["choices"][0]["message"]["content"].strip()
                hooks = [h.strip("- ") for h in text.splitlines() if h.strip()][:10]
        except Exception as e:
            print(f"[generate_captions] openai failed: {e}")
            # Use fallback if AI fails
            hooks = [
                "Flip fast: This week’s top resell winners.",
                "Trending now. High demand, low supply.",
                "Stop guessing. Start flipping.",
                "10x better sourcing in 5 minutes.",
                "Snapshots of what’s moving today.",
                "Buy right. Sell faster.",
                "Margin-first picks for this week.",
                "Proven demand. Fresh every week.",
                "Beat the market with the pack.",
                "Skim the top. Profit the gap.",
            ]

    with open(out / "captions.json", "w", encoding="utf-8") as f:
        json.dump({"hooks": hooks}, f, indent=2)
    print("[generate_captions] wrote out/captions.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# TD-AUTO: END generate-captions


