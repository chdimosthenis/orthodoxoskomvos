"""Generate PNG favicons from the SVG geometry.

Mirrors public/favicon.svg (32x32 viewBox, eight-pointed Orthodox cross in
#b08d57). Renders at high resolution, then downsamples for crisp results at
each target favicon size.

Google's favicon-in-search guidance recommends a multiple of 48x48; we emit
96 and 192 to cover desktop SERP + Android home-screen suggestions, and a
180x180 apple-touch-icon on a parchment ground for iOS home-screen pinning.

    python scripts/_make_favicons.py

Outputs:
    public/favicon-96.png         (transparent, 96x96)
    public/favicon-192.png        (transparent, 192x192)
    public/apple-touch-icon.png   (parchment ground, 180x180)
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "public"

GOLD = (176, 141, 87, 255)          # #b08d57 — matches Header brand-mark
PARCHMENT = (250, 246, 237, 255)    # #faf6ed — apple-touch-icon ground

SCALE = 32  # SVG viewBox is 32x32 → render at 32*32 = 1024px then downsample


def render_cross(size: int, bg: tuple[int, int, int, int] | None = None) -> Image.Image:
    canvas = SCALE * 32
    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0) if bg is None else bg)
    drw = ImageDraw.Draw(img)
    s = SCALE

    drw.rectangle([14.6 * s, 2.5 * s, (14.6 + 2.8) * s, (2.5 + 27) * s], fill=GOLD)
    drw.rectangle([11.2 * s, 6.5 * s, (11.2 + 9.6) * s, (6.5 + 1.8) * s], fill=GOLD)
    drw.rectangle([7.6 * s, 11 * s, (7.6 + 16.8) * s, (11 + 2.6) * s], fill=GOLD)

    bar = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    ImageDraw.Draw(bar).rectangle(
        [9.6 * s, 20.4 * s, (9.6 + 12.8) * s, (20.4 + 1.8) * s], fill=GOLD
    )
    bar = bar.rotate(15, center=(16 * s, 21.3 * s), resample=Image.BICUBIC)
    img.alpha_composite(bar)

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    targets = [
        ("favicon-96.png", 96, None),
        ("favicon-192.png", 192, None),
        ("apple-touch-icon.png", 180, PARCHMENT),
    ]
    for fname, size, bg in targets:
        out = OUT_DIR / fname
        render_cross(size, bg=bg).save(out, "PNG", optimize=True)
        print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
