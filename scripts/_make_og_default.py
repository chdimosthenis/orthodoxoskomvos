"""Generate public/og-default.png — branded 1200x630 social-share image.

SVG og:image is unreliable across social platforms (Facebook, LinkedIn,
Slack reject it). This script renders a PNG with the same aesthetic as
public/og-default.svg using Pillow. Run once, or after brand changes.

    python scripts/_make_og_default.py
"""
from __future__ import annotations
import math
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


def draw_orthodox_cross(drw: ImageDraw.ImageDraw, cx: float, cy: float,
                        scale: float = 6.5, color: tuple[int, int, int] = BURGUNDY) -> None:
    """Draw the brand 8-pointed Orthodox cross centered at (cx, cy).

    Geometry mirrors public/favicon.svg (32x32 viewBox) — vertical post,
    titulus (top crossbar), main crossbar, slanted suppedaneum. Drawn as
    PIL primitives so we don't depend on any font having ☧ (most don't —
    Georgia renders it as tofu, which is what shipped on og-default.png
    pre-2026-05-15).
    """
    def to_canvas(x: float, y: float) -> tuple[float, float]:
        # (16, 16) in the viewBox maps to (cx, cy) on the canvas
        return (cx + (x - 16) * scale, cy + (y - 16) * scale)

    def filled_rect(x: float, y: float, w: float, h: float) -> None:
        x1, y1 = to_canvas(x, y)
        x2, y2 = to_canvas(x + w, y + h)
        drw.rectangle([x1, y1, x2, y2], fill=color)

    # Vertical post
    filled_rect(14.6, 2.5, 2.8, 27)
    # Top crossbar (titulus)
    filled_rect(11.2, 6.5, 9.6, 1.8)
    # Main crossbar
    filled_rect(7.6, 11, 16.8, 2.6)
    # Slanted suppedaneum — rotate -15° around (16, 21.3)
    angle = math.radians(-15)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    rx, ry = 16, 21.3
    corners_vb = [(9.6, 20.4), (22.4, 20.4), (22.4, 22.2), (9.6, 22.2)]
    rotated_canvas: list[tuple[float, float]] = []
    for x, y in corners_vb:
        dx, dy = x - rx, y - ry
        nx = rx + dx * cos_a - dy * sin_a
        ny = ry + dx * sin_a + dy * cos_a
        rotated_canvas.append(to_canvas(nx, ny))
    drw.polygon(rotated_canvas, fill=color)


def main() -> None:
    img = gradient_fill()
    drw = ImageDraw.Draw(img)

    # Inner ornamental border
    drw.rectangle([40, 40, W - 40, H - 40], outline=GOLD, width=2)

    # Prefer Palatino Linotype / Cambria / Times — all carry the
    # Greek Extended (polytonic) block, in case the brand title or
    # tagline ever uses breathing marks. Georgia is monotonic-only.
    font_title = find_font(
        ["palab.ttf", "cambriab.ttf", "timesbd.ttf",
         "georgiab.ttf", "DejaVuSerif-Bold.ttf"], 84,
    )
    font_tagline = find_font(
        ["pala.ttf", "cambria.ttc", "times.ttf",
         "georgia.ttf", "DejaVuSerif.ttf"], 32,
    )

    # Eight-pointed Orthodox cross — drawn (not glyph) so it always renders.
    draw_orthodox_cross(drw, cx=W / 2, cy=200, scale=6.5, color=BURGUNDY)

    # Brand title — Greek
    title = "Ορθόδοξος Κόμβος"
    bbox = drw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    drw.text(((W - tw) / 2 - bbox[0], 340), title, fill=INK, font=font_title)

    # Tagline
    tagline = "Κείμενα · Βίοι αγίων · Ακολουθίες"
    bbox = drw.textbbox((0, 0), tagline, font=font_tagline)
    tlw = bbox[2] - bbox[0]
    drw.text(((W - tlw) / 2 - bbox[0], 460), tagline, fill=MUTED, font=font_tagline)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
