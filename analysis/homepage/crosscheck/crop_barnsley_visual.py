#!/usr/bin/env python3
"""Crop Barnsley features directly from the saved 40-barnsley.png using
visually-determined Y coordinates. Falls back to direct PNG cropping when
the page DOM doesn't expose the content via getBoundingClientRect (lazy
loading / virtual scrolling)."""

from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
IMG_DIR = ROOT / "img"
SCREENSHOTS_DIR = ROOT.parent / "screenshots"

SCREENSHOT = SCREENSHOTS_DIR / "40-barnsley.png"

# Y coordinates derived from visual inspection of the 1440x5206 capture.
CROPS = {
    "secondary_editorial_strip_below_hero": (0, 1390, 1440, 1860),
    "b2b_partnerships": (90, 4360, 730, 4800),
}


def main():
    img = Image.open(SCREENSHOT)
    print(f"Source: {SCREENSHOT.name} ({img.size[0]}x{img.size[1]})")
    for feature, (x1, y1, x2, y2) in CROPS.items():
        cropped = img.crop((x1, y1, x2, y2))
        out = IMG_DIR / f"barnsley_{feature}.png"
        cropped.save(out)
        print(f"  [OK] {feature}: {x2-x1}x{y2-y1} -> {out.name}")


if __name__ == "__main__":
    main()
