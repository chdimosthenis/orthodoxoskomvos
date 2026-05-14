"""Generate public/og-default.png — branded 1200x630 social-share image.

SVG og:image is unreliable across social platforms (Facebook, LinkedIn,
Slack reject it). This script renders a PNG with the same aesthetic as
public/og-default.svg using Pillow. Run once, or after brand changes.

    python scripts/_make_og_default.py
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "og-default.png"

W, H = 1200, 630
PARCHMENT_TOP = (250, 246, 237)   # #faf6ed
PARCHMENT_BOT = (240, 233, 212)   # #f0e9d4
GOLD = (176, 141, 87)             # #b08d57
BURGUNDY = (107, 27, 44)          # #6b1b2c
INK = (26, 20, 16)                # #1a1410
MUTED = (110, 98, 88)             # #6e6258


def gradient_fill() -> Image.Image:
    """Diagonal-ish gradient, parchment-light to parchment-warm."""
    img = Image.new("RGB", (W, H), PARCHMENT_TOP)
    px = img.load()
    assert px is not None
    for y in range(H):
        t = y / (H - 1)
        for x in range(W):
            tx = x / (W - 1)
            mix = (t + tx) / 2
            px[x, y] = (
                round(PARCHMENT_TOP[0] * (1 - mix) + PARCHMENT_BOT[0] * mix),
                round(PARCHMENT_TOP[1] * (1 - mix) + PARCHMENT_BOT[1] * mix),
                round(PARCHMENT_TOP[2] * (1 - mix) + PARCHMENT_BOT[2] * mix),
            )
    return img


def find_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try a list of font names/paths; fall back to PIL default."""
    import os
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
        if os.name == "nt":
            for prefix in (r"C:\Windows\Fonts",):
                p = os.path.join(prefix, name)
                if os.path.exists(p):
                    try:
                        return ImageFont.truetype(p, size)
                    except (OSError, IOError):
                        continue
    return ImageFont.load_default()


def main() -> None:
    img = gradient_fill()
    drw = ImageDraw.Draw(img)

    # Inner ornamental border
    drw.rectangle([40, 40, W - 40, H - 40], outline=GOLD, width=2)

    # Use Georgia / DejaVu for Greek glyph coverage
    font_symbol = find_font(["georgia.ttf", "georgiab.ttf", "DejaVuSerif.ttf"], 130)
    font_title = find_font(["georgiab.ttf", "georgia.ttf", "DejaVuSerif-Bold.ttf"], 84)
    font_tagline = find_font(["georgia.ttf", "DejaVuSerif.ttf"], 32)

    # Christogram (Chi-Rho)
    symbol = "☧"
    bbox = drw.textbbox((0, 0), symbol, font=font_symbol)
    sw = bbox[2] - bbox[0]
    sh = bbox[3] - bbox[1]
    drw.text(((W - sw) / 2 - bbox[0], 200 - sh / 2 - bbox[1]), symbol, fill=BURGUNDY, font=font_symbol)

    # Brand title — Greek
    title = "Ορθόδοξος Κόμβος"
    bbox = drw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    drw.text(((W - tw) / 2 - bbox[0], 340), title, fill=INK, font=font_title)

    # Tagline
    tagline = "Πατερικά κείμενα · Βίοι αγίων · Ακολουθίες"
    bbox = drw.textbbox((0, 0), tagline, font=font_tagline)
    tlw = bbox[2] - bbox[0]
    drw.text(((W - tlw) / 2 - bbox[0], 460), tagline, fill=MUTED, font=font_tagline)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
