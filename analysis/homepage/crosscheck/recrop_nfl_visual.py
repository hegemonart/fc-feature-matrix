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
CROPS = {
    # NFL DRAFT picks strip + GP "Watch Every Game" black bar above the
    # main header.
    "persistent_bar_above_header": (0, 0, 1440, 130),

    # Top-right of header — "Tickets" / "Sign In". Crop tightly.
    "tickets_shortcut_in_header": (915, 130, 1015, 200),
    "login_account": (1290, 130, 1410, 200),

    # Hard Knocks hero — left column. Shows HBO ORIGINAL, HARD KNOCKS,
    # TRAINING CAMP, BUFFALO BILLS, GAME PASS, DAZN, HBO max sponsor
    # branding + "DAZN.com/NFL" CTA.
    "brand_sponsor_highlighted_in_hero": (280, 200, 985, 820),
    "episodic_docu_series": (280, 200, 985, 820),
    "paid_membership": (280, 200, 985, 820),

    # NEWS column — right side of hero, with NEWS / MY TEAM tabs and
    # 10+ headline items.
    "dedicated_news_section": (990, 200, 1435, 820),
    "news_rich_structure": (990, 200, 1435, 820),

    # Baldy's "rookies in best position" video block — left column,
    # large video player with play button (>33% width).
    "homepage_video_block": (280, 830, 985, 1190),

    # Super Bowl Replays SEA vs NE — past-match content block (heritage).
    "heritage_past_content": (100, 1390, 985, 1620),

    # International Football Development right-column block — has
    # PLAYER PATHWAY × NFL ACADEMY × NFL FLAG co-branded ribbon = sponsor
    # placement inside homepage body content.
    "in_content_sponsor": (1000, 1770, 1430, 2090),

    # Same GP "WATCH EVERY GAME WITH GAME PASS" persistent bar promotes
    # the streaming app — qualifies as club_tv_app_promo proof.
    "club_tv_app_promo": (0, 0, 1440, 30),

    # UK AND IRELAND PLAYERS heading + 3x2 grid (left column).
    "player_roster_preview": (100, 1920, 985, 2580),
    "individual_player_cards": (100, 2050, 985, 2580),

    # FANTASY heading + 3-card row.
    "predictor_fantasy": (100, 2580, 985, 2980),

    # Footer "Download the App" — Apple + Google Play badges (right
    # side of footer columns).
    "app_store_badges": (1180, 3770, 1340, 3970),

    # Social icons row in footer (FB / YT / IG / TT / SC / X / LinkedIn).
    "social_links_in_footer": (80, 4420, 290, 4470),
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
