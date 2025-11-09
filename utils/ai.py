import os, json, re
from pathlib import Path
from trenddrop.utils.env_loader import load_env_once

# Ensure root .env is loaded
ENV_PATH = load_env_once()
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


def _fallback_marketing_copy(p: Dict) -> Dict:
    """Heuristic copy when OpenAI is unavailable or errors."""
    raw_title = str(p.get("title", "")).strip()
    currency = p.get("currency", "USD")
    price = p.get("price")
    price_text = f"{currency} {price:.2f}" if isinstance(price, (int, float)) else (f"{currency} {price}" if price else "")

    # Headline: trim and add a leading emoji when obvious
    headline = raw_title
    # Simplify noisy eBay titles
    headline = re.sub(r"\b(New|Brand\s*New|Hot|Sale|4IN1|3IN1|2PCS|Lot|Bundle)\b", "", headline, flags=re.I)
    headline = re.sub(r"\s{2,}", " ", headline).strip()
    headline = headline[:90]

    # Emoji pack guess
    text = f"{raw_title} {p.get('keyword','')}".lower()
    emojis = ""
    if any(k in text for k in ["game", "gaming", "xbox", "ps5", "keyboard", "mouse"]):
        emojis = "🕹️🎮✨"
    elif any(k in text for k in ["dress", "jacket", "sneaker", "fashion", "shirt", "jean"]):
        emojis = "👗👟✨"
    elif any(k in text for k in ["sofa", "lamp", "home", "kitchen", "cook", "vacuum"]):
        emojis = "🏠🛋️✨"
    else:
        emojis = "🔥✨"

    # Blurb: add urgency
    blurb_bits = ["Limited stock—grab it now!"]
    if price_text:
        blurb_bits.insert(0, f"{price_text} steal.")
    blurb = " ".join(blurb_bits)

    # Add a leading emoji to headline
    lead = emojis.split(" ")[0] if " " in emojis else emojis[:2]
    if lead:
        headline = f"{lead} {headline}"

    return {"headline": headline, "blurb": blurb, "emojis": emojis}


def marketing_copy_for(p: Dict) -> Dict:
    """
    Generate short, punchy marketing copy for a product:
      - headline: concise hook (<= 80-90 chars)
      - blurb: 1–2 sentences with urgency and CTA
      - emojis: optional emoji pack (e.g., gaming 🕹️, home 🏠, fashion 👗)

    Returns a dict with keys: headline, blurb, emojis
    """
    if not OPENAI_API_KEY or not openai:
        return _fallback_marketing_copy(p)

    raw_title = str(p.get("title", ""))
    currency = p.get("currency", "USD")
    price = p.get("price", "")
    topic = ", ".join(p.get("tags", []) or ([p.get("keyword")] if p.get("keyword") else []))

    sys_prompt = (
        "You are a conversion-focused copywriter for an affiliate deals site. "
        "Write exciting but truthful copy."
    )

    user_prompt = (
        "Create concise marketing copy with this structure and return ONLY compact JSON.\n"
        "Rules:\n"
        "- headline: short, punchy, <= 90 chars; can include a leading emoji.\n"
        "- blurb: 1–2 sentences, urgency (limited time/stock), clear benefit + CTA.\n"
        "- emojis: optional 2–3 emojis relevant to category; prefer from {gaming: 🕹️🎮, home: 🏠🛋️, fashion: 👗👟}.\n"
        "- Keep it clean, no quotes or markdown.\n"
        "Product:\n"
        f"- title: {raw_title}\n"
        f"- price: {currency} {price}\n"
        f"- topic: {topic}\n\n"
        "Respond as JSON with keys exactly: headline, blurb, emojis."
    )

    try:
        if hasattr(openai, "api_key"):
            openai.api_key = OPENAI_API_KEY
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_tokens=200,
        )
        content = resp.choices[0].message.content.strip()
        # Extract JSON (model may include stray text)
        match = re.search(r"\{[\s\S]*\}$", content)
        json_text = match.group(0) if match else content
        data = json.loads(json_text)
        headline = str(data.get("headline", "")).strip() or None
        blurb = str(data.get("blurb", "")).strip() or None
        emojis = str(data.get("emojis", "")).strip()
        if not (headline and blurb):
            raise ValueError("incomplete ai response")
        return {"headline": headline[:90], "blurb": blurb[:240], "emojis": emojis[:16]}
    except Exception:
        return _fallback_marketing_copy(p)


