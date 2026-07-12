"""
Downloader for arcamax.com comics:
  - B.C.             (id: bc)
  - Bizarro          (id: biz)
  - Jerry King Cartoons (id: jkc)
  - The Fortune Teller  (id: tft)

When this breaks:
  - Check last_known_good_cache/{comic_id}.html vs the current page source
  - Look for an <img> tag with a data-zoom-image attribute — that's how
    arcamax.com marks the full-resolution comic image
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


async def download_arcamax(
    comic_config: dict,
    images_dir: Path,
    cache_dir: Path,
    **kwargs,
) -> ComicResult:
    comic_id = comic_config["id"]
    comic_name = comic_config["name"]
    url = comic_config["url"]
    prefix = comic_config["prefix"]
    ext = comic_config.get("extension", "gif")

    today = date.today().strftime("%Y%m%d")
    filename = f"{prefix}-{today}.{ext}"
    image_path = images_dir / filename

    result = ComicResult(comic_id=comic_id, comic_name=comic_name, page_url=url)

    if image_path.exists() and image_path.stat().st_size > 0:
        print(f"  [{comic_name}] Already downloaded: {filename}")
        result.images.append(ImageResult(cid=comic_id, image_path=image_path))
        return result

    print(f"  [{comic_name}] Fetching {url} ...")
    try:
        response = requests.get(url, headers=_HEADERS, timeout=30)
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, "html.parser")

        # arcamax marks the full-res image with data-zoom-image
        img_tag = soup.find("img", attrs={"data-zoom-image": True})
        if not img_tag:
            raise RuntimeError("No <img data-zoom-image=...> found on page")

        img_url = img_tag.get("data-zoom-image") or img_tag.get("src")
        if not img_url:
            raise RuntimeError("data-zoom-image attribute present but empty")

        r = requests.get(
            img_url, headers={**_HEADERS, "Referer": url}, timeout=30
        )
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
