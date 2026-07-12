"""
Downloader for gocomics.com comics (Loose Parts, Calvin and Hobbes, Off the Mark,
F Minus, Daddy's Home, and any future gocomics.com additions).

gocomics.com uses a JavaScript-heavy React frontend, so Playwright is required.
A shared Playwright page is passed in from main.py so all gocomics downloads
reuse one browser session.

When this breaks:
  - Check config.toml: the 'selector' field for the failing comic
  - Check last_known_good_cache/{comic_id}.html vs the current page source
    to see what changed in the DOM structure
  - The FALLBACK_SELECTORS list below provides additional candidates to try
"""

import asyncio
import requests
from datetime import date
from pathlib import Path

from .base import ComicResult, ImageResult

# If the primary selector (from config.toml) fails, these are tried in order.
# featureassets.gocomics.com is their CDN — that part of the URL is stable.
FALLBACK_SELECTORS = [
    'picture img[src*="featureassets"]',
    'img[src*="featureassets.gocomics.com"]',
    '[class*="Comic"] img[src*="featureassets"]',
    'article img[src*="featureassets"]',
]

_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/116.0.0.0 Safari/537.36"
    )
}


async def _find_comic_image(page, primary_selector: str, comic_name: str):
    """Try the configured selector then automatic fallbacks."""
    for selector in [primary_selector] + FALLBACK_SELECTORS:
        try:
            element = await page.wait_for_selector(selector, timeout=8000)
            if element:
                if selector != primary_selector:
                    print(
                        f"  [{comic_name}] Primary selector failed; "
                        f"matched fallback: {selector!r}"
                    )
                return element, selector
        except Exception:
            continue
    return None, None


async def download_gocomic(
    comic_config: dict,
    images_dir: Path,
    cache_dir: Path,
    *,
    page,
    **kwargs,
) -> ComicResult:
    comic_id = comic_config["id"]
    comic_name = comic_config["name"]
    url = comic_config["url"]
    prefix = comic_config["prefix"]
    ext = comic_config.get("extension", "gif")
    selector = comic_config.get("selector", 'img[class*="Comic_comic__image"]')

    today = date.today().strftime("%Y%m%d")
    filename = f"{prefix}-{today}.{ext}"
    image_path = images_dir / filename

    result = ComicResult(comic_id=comic_id, comic_name=comic_name, page_url=url)

    if image_path.exists() and image_path.stat().st_size > 0:
        print(f"  [{comic_name}] Already downloaded: {filename}")
        result.images.append(ImageResult(cid=comic_id, image_path=image_path))
        return result

    print(f"  [{comic_name}] Navigating to {url} ...")
    try:
        try:
            await page.goto(url, wait_until="load", timeout=30000)
        except Exception:
            print(f"  [{comic_name}] Page load timed out — attempting anyway ...")
        await asyncio.sleep(2)

        element, matched_selector = await _find_comic_image(page, selector, comic_name)

        if element is None:
            # Save debug artifacts before raising
            html = await page.content()
            debug_html = cache_dir / f"{comic_id}_debug.html"
            debug_png = images_dir / f"{comic_id}_debug.png"
            debug_html.write_text(html, encoding="utf-8")
            await page.screenshot(path=str(debug_png))
            raise RuntimeError(
                f"Comic image not found with primary selector {selector!r} "
                f"or any fallback. Debug HTML: {debug_html}  Screenshot: {debug_png}"
            )

        img_url = await element.get_attribute("src")
        if not img_url:
            raise RuntimeError("Image element found but src attribute is empty")

        r = requests.get(img_url, headers=_REQUEST_HEADERS, timeout=30)
        r.raise_for_status()
        image_path.write_bytes(r.content)

        # Save cache only on success so last_known_good is always a working version
        html = await page.content()
        (cache_dir / f"{comic_id}.html").write_text(html, encoding="utf-8")

        print(f"  [{comic_name}] Downloaded: {filename}")
        result.images.append(ImageResult(cid=comic_id, image_path=image_path))

    except Exception as e:
        result.error = str(e)
        print(f"  [{comic_name}] ERROR: {e}")

    return result
