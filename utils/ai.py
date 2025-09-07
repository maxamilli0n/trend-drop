import os
from typing import Dict

try:
    import openai  # type: ignore
except Exception:
    openai = None  # type: ignore

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

PROMPT = """You write short hypey product captions (<180 chars) with an emoji and a CTA.
Return just the sentence, no extra quotes.
Title: {title}
Price: {currency} {price}
"""


def caption_for(p: Dict) -> str:
    if not OPENAI_API_KEY or not openai:
        title = str(p.get("title", ""))[:120]
        currency = p.get("currency", "USD")
        price = p.get("price", "")
        return f"{title} • {currency} {price}"
    try:
        if hasattr(openai, "api_key"):
            openai.api_key = OPENAI_API_KEY
        text = PROMPT.format(title=p.get("title", ""), currency=p.get("currency", "USD"), price=p.get("price", ""))
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": text}],
            temperature=0.7,
            max_tokens=80,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        title = str(p.get("title", ""))[:120]
        currency = p.get("currency", "USD")
        price = p.get("price", "")
        return f"{title} • {currency} {price}"


