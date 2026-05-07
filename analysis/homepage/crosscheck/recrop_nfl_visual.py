#!/usr/bin/env python3
"""Re-crop ALL NFL cropouts directly from 39-nfl.png using visually-determined
coordinates. Replaces the prior recipe-based crops which produced wrong
regions (e.g. dedicated_news_section showed FANTASY).

Source: 1440x4504 PNG layout, NFL.com homepage 2026-05-07.
"""

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
IMG_DIR = ROOT / "img"
SCREENSHOTS_DIR = ROOT.parent / "screenshots"

SCREENSHOT = SCREENSHOTS_DIR / "39-nfl.png"

# (left, top, right, bottom) in 1440x4504 source.
# All Y boundaries verified by sampling Y strips and visual inspection.
CROPS = {
    # NFL DRAFT picks strip + GP "Watch Every Game" black bar above the
    # main header. Y 0-125 — stop at header divider line.
    "persistent_bar_above_header": (0, 0, 1440, 118),

    # Top-right of header — "Tickets" / "Sign In" links.
    # Header proper occupies Y 130-180.
    "tickets_shortcut_in_header": (920, 130, 1010, 180),
    "login_account": (1280, 130, 1395, 180),

    # Hard Knocks hero — left column (X 230-985, Y 200-820). Includes
    # HBO ORIGINAL header, HARD KNOCKS / BUFFALO BILLS title, GAME PASS
    # × DAZN × HBO max sponsor lockup, DAZN.com/NFL CTA, caption.
    "brand_sponsor_highlighted_in_hero": (230, 200, 985, 820),
    "episodic_docu_series": (230, 200, 985, 820),
    "paid_membership": (230, 200, 985, 820),

    # NEWS column — right side of hero (X 990-1435, Y 200-820). NEWS /
    # MY TEAM tabs + 10+ headlines.
    "dedicated_news_section": (975, 200, 1435, 820),
    "news_rich_structure": (975, 200, 1435, 820),

    # Baldy's "rookies in best position" video block — left column.
    # Video player + title overlay + caption.
    "homepage_video_block": (230, 855, 985, 1240),

    # Super Bowl Replays SEA vs NE — past-match content block. Wide
    # because the GP-prefix heading starts at X 100, banner at X 230.
    "heritage_past_content": (95, 1395, 985, 1620),

    # International Football Development right-column block — has
    # PLAYER PATHWAY × NFL ACADEMY × NFL FLAG co-branded ribbon =
    # in-content sponsor placement.
    "in_content_sponsor": (985, 1770, 1430, 2090),

    # GP "WATCH EVERY GAME WITH GAME PASS" persistent bar promotes the
    # streaming app — qualifies as club_tv_app_promo proof.
    "club_tv_app_promo": (0, 0, 1440, 32),

    # UK AND IRELAND PLAYERS heading (X starts ~290 centered) + 3x2
    # player grid (X 95-985, cards visible from Y 1990).
    "player_roster_preview": (95, 1925, 985, 2580),
    # Tighter — just the 6 player cards without the section heading.
    "individual_player_cards": (95, 1990, 985, 2580),

    # FANTASY heading + 3-card row.
    "predictor_fantasy": (95, 2615, 985, 2970),

    # Footer "Download the App" + Apple App Store + Google Play
    # badges, vertically stacked.
    "app_store_badges": (1180, 3775, 1340, 3970),

    # Social icons row in footer — FB / YT / IG / TT / SC / X / LinkedIn.
    "social_links_in_footer": (80, 4425, 290, 4470),
}


def main():
    img = Image.open(SCREENSHOT)
    print(f"Source: {SCREENSHOT.name} ({img.size[0]}x{img.size[1]})")
    for feature, box in CROPS.items():
        cropped = img.crop(box)
        out = IMG_DIR / f"nfl_{feature}.png"
        cropped.save(out)
        w, h = cropped.size
        print(f"  [OK] nfl_{feature}.png  {w}x{h}")


if __name__ == "__main__":
    main()
