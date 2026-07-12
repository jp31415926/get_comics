"""
Downloader for xkcd (xkcd.com).

When this breaks:
  - Check last_known_good_cache/xkcd.html vs the current page source
  - Look for <div id="comic"> containing an <img> — xkcd's structure
    has been stable for many years
"""

import requests
from bs4 import BeautifulSoup
from datetime import date
from pathlib import Path

from .base import ComicResult, ImageResult

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/116.0.0.0 Safari/537.36"
    )
}


async def download_xkcd(
    comic_config: dict,
    images_dir: Path,
    cache_dir: Path,
    **kwargs,
) -> ComicResult:
    comic_id = comic_config["id"]
    comic_name = comic_config["name"]
    url = comic_config["url"]
    prefix = comic_config["prefix"]

    today = date.today().strftime("%Y%m%d")
    result = ComicResult(comic_id=comic_id, comic_name=comic_name, page_url=url)

    # xkcd images can be .png or .jpg — check for any existing file with today's date
    existing = list(images_dir.glob(f"{prefix}-{today}.*"))
    if existing:
        print(f"  [{comic_name}] Already downloaded: {existing[0].name}")
        result.images.append(ImageResult(cid=comic_id, image_path=existing[0]))
        return result

    print(f"  [{comic_name}] Fetching {url} ...")
    try:
        response = requests.get(url, headers=_HEADERS, timeout=30)
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, "html.parser")

        comic_div = soup.find("div", id="comic")
        if not comic_div:
            raise RuntimeError("No <div id='comic'> found on page")

        img_tag = comic_div.find("img")
        if not img_tag:
            raise RuntimeError("No <img> inside <div id='comic'>")

        img_src = img_tag.get("src", "")
        if img_src.startswith("//"):
            img_src = "https:" + img_src
        if not img_src:
            raise RuntimeError("img src is empty")

        # Use the actual file extension from the URL
        actual_ext = img_src.rsplit(".", 1)[-1].lower() if "." in img_src else "png"
        filename = f"{prefix}-{today}.{actual_ext}"
        image_path = images_dir / filename

        r = requests.get(img_src, headers=_HEADERS, timeout=30)
        r.raise_for_status()
        image_path.write_bytes(r.content)

        # Save cache only on success
        (cache_dir / f"{comic_id}.html").write_text(html, encoding="utf-8")

        print(f"  [{comic_name}] Downloaded: {filename}")
        result.images.append(ImageResult(cid=comic_id, image_path=image_path))

    except Exception as e:
        result.error = str(e)
        print(f"  [{comic_name}] ERROR: {e}")

    return result
