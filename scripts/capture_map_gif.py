"""
Capture the interactive Leaflet map animation as a GIF.
Usage: python scripts/capture_map_gif.py
Output: docs/maps/suisse-romande-animation.gif
"""

import asyncio
import io
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright

HTML_FILE = Path(__file__).parent.parent / "docs/maps/interactive-map.html"
OUTPUT_GIF = Path(__file__).parent.parent / "docs/maps/suisse-romande-animation.gif"

# Capture a screenshot every N ms during the animation
CAPTURE_INTERVAL_MS = 600
TOTAL_DURATION_MS   = 14000   # animation is ~12s, capture a bit more
WIDTH, HEIGHT       = 1280, 720


async def capture():
    frames: list[Image.Image] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page    = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})

        # Open the local HTML file
        await page.goto(HTML_FILE.as_uri())
        print(f"Opened: {HTML_FILE.name}")

        # Wait for Leaflet tiles to start loading
        await page.wait_for_timeout(1500)

        elapsed = 0
        while elapsed < TOTAL_DURATION_MS:
            screenshot = await page.screenshot(type="png")
            img = Image.open(io.BytesIO(screenshot)).convert("RGB")
            frames.append(img)
            print(f"  Frame {len(frames):>3}  ({elapsed/1000:.1f}s)")
            await page.wait_for_timeout(CAPTURE_INTERVAL_MS)
            elapsed += CAPTURE_INTERVAL_MS

        await browser.close()

    print(f"\nCaptured {len(frames)} frames — building GIF…")

    OUTPUT_GIF.parent.mkdir(parents=True, exist_ok=True)

    # Resize for smaller file size
    thumb_w, thumb_h = 960, 540
    frames = [f.resize((thumb_w, thumb_h), Image.LANCZOS) for f in frames]

    frames[0].save(
        OUTPUT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=CAPTURE_INTERVAL_MS,
        loop=0,
        optimize=True,
    )

    size_mb = OUTPUT_GIF.stat().st_size / 1_000_000
    print(f"Saved: {OUTPUT_GIF}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    asyncio.run(capture())
