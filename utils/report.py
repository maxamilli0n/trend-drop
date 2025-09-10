import os, time, requests
from typing import List, Dict, Optional

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
except Exception:
    letter = None  # type: ignore
    ImageReader = None  # type: ignore
    canvas = None  # type: ignore
    colors = None  # type: ignore

from utils.db import sb


def _safe_text(val: Optional[str]) -> str:
    return (val or "").strip()


def _fetch_image_bytes(url: str) -> Optional[bytes]:
    try:
        r = requests.get(url, timeout=12)
        if r.status_code == 200 and r.content:
            return r.content
    except Exception:
        pass
    return None


def generate_weekly_pdf(products: List[Dict], outfile_path: str) -> None:
    """
    Build a simple Top 10 PDF: cover + one product per page (image, headline, price, link).
    """
    if canvas is None or letter is None:
        # No reportlab installed; write a very simple text fallback
        with open(outfile_path, "wb") as f:
            f.write(b"TrendDrop Weekly Top 10\n\n")
            for i, p in enumerate(products[:10], start=1):
                line = f"{i}. {_safe_text(p.get('headline') or p.get('title'))} — {_safe_text(str(p.get('currency') or 'USD'))} {_safe_text(str(p.get('price') or ''))} -> {_safe_text(p.get('url'))}\n".encode("utf-8")
                f.write(line)
        return

    c = canvas.Canvas(outfile_path, pagesize=letter)
    width, height = letter

    # Cover page
    c.setFillColorRGB(0.06, 0.09, 0.16)  # dark bg
    c.rect(0, 0, width, height, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 36)
    c.drawString(72, height - 144, "TrendDrop")
    c.setFont("Helvetica", 18)
    c.drawString(72, height - 180, "Weekly Top 10 — Today’s Trending Finds")
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.whitesmoke)
    c.drawString(72, 72, time.strftime("Generated %Y-%m-%d", time.gmtime()))
    c.showPage()

    # Product pages (one per product for clarity)
    for i, p in enumerate(products[:10], start=1):
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 18)
        title = _safe_text(p.get("headline") or p.get("title"))[:100]
        c.drawString(72, height - 90, f"#{i}  {title}")

        # Price
        c.setFont("Helvetica", 12)
        currency = _safe_text(p.get("currency") or "USD")
        price = p.get("price")
        price_text = f"{currency} {price:.2f}" if isinstance(price, (int, float)) else f"{currency} {_safe_text(str(price))}"
        c.drawString(72, height - 120, price_text)

        # Image (try to fit into a 4:3 box)
        img_y_top = height - 140
        box_w, box_h = width - 144, 360
        img_url = _safe_text(p.get("image_url"))
        img_bytes = _fetch_image_bytes(img_url) if img_url else None
        if img_bytes:
            try:
                img = ImageReader(img_bytes)
                iw, ih = img.getSize()
                scale = min(box_w / iw, box_h / ih)
                dw, dh = iw * scale, ih * scale
                x = 72 + (box_w - dw) / 2
                y = img_y_top - dh
                c.drawImage(img, x, y, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

        # Link
        url = _safe_text(p.get("url"))
        if url:
            y_link = 72
            c.setFillColor(colors.blue)
            c.setFont("Helvetica", 12)
            link_text = "View product"
            c.drawString(72, y_link, link_text)
            text_w = c.stringWidth(link_text, "Helvetica", 12)
            c.linkURL(url, (72, y_link - 2, 72 + text_w, y_link + 10))
            c.setFillColor(colors.black)

        c.showPage()

    c.save()


def upload_pdf_to_supabase(local_path: str, storage_path: str) -> Optional[str]:
    """Upload PDF to Supabase Storage bucket 'reports'. Return public URL if possible."""
    client = sb()
    if not client:
        return None
    try:
        # Try to create bucket (idempotent if exists)
        try:
            client.storage.create_bucket("reports", public=True)
        except Exception:
            pass
        # Upload
        with open(local_path, "rb") as f:
            client.storage.from_("reports").upload(
                path=storage_path,
                file=f,
                file_options={"contentType": "application/pdf", "upsert": True},
            )
        # Get public URL
        pub = client.storage.from_("reports").get_public_url(storage_path)
        return pub.get("publicUrl") if isinstance(pub, dict) else pub
    except Exception:
        return None


