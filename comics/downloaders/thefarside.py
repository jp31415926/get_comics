"""
Downloader for The Far Side (thefarside.com).

Different from all other comics:
  - Fetches up to 2 images per day (max_images in config.toml)
  - Each image may have an optional figcaption
  - Images are embedded with CIDs: "tfs" and "tfs2"
  - Files are named: tfs-YYYYMMDD.jpg and tfs2-YYYYMMDD.jpg

Page structure (as of 2026-03):
  <div class="card tfs-comic js-comic">
    <div class="tfs-comic__image">
      <img data-src="https://featureassets.amuniversal.com/assets/..." />
      <!-- src is a lazy-load SVG placeholder; real URL is in data-src -->
    </div>
    <figure class="figure tfs-comic__caption">
      <figcaption class="figure-caption">optional caption text</figcaption>
    </figure>
  </div>

When this breaks:
  - Check last_known_good_cache/tfs.html vs the current page source
  - Look for the container holding each comic (currently div.tfs-comic)
  - Image URL is in data-src (lazy loaded), CDN is featureassets.amuniversal.com
  - Caption is in a sibling <figure> element within the same comic container
"""

import re
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

_CDN_DOMAIN = "featureassets.amuniversal.com"
_COMIC_CONTAINER_CLASS = "tfs-comic"


async def download_thefarside(
    comic_config: dict,
    images_dir: Path,
    cache_dir: Path,
    **kwargs,
) -> ComicResult:
    comic_id = comic_config["id"]
    comic_name = comic_config["name"]
    url = comic_config["url"]
    prefix = comic_config["prefix"]
    ext = comic_config.get("extension", "jpg")
    max_images = comic_config.get("max_images", 2)

    today = date.today().strftime("%Y%m%d")
    result = ComicResult(comic_id=comic_id, comic_name=comic_name, page_url=url)

    def slot_cid(i):
        return comic_id if i == 0 else f"{comic_id}{i + 1}"

    def slot_filename(i):
        return f"{prefix}-{today}.{ext}" if i == 0 else f"{prefix}{i + 1}-{today}.{ext}"

    # If all expected files already exist, skip download
    cached_images = []
    for i in range(max_images):
        p = images_dir / slot_filename(i)
        if p.exists() and p.stat().st_size > 0:
            cached_images.append(ImageResult(cid=slot_cid(i), image_path=p))
        else:
            cached_images = []
            break

    if cached_images:
        print(f"  [{comic_name}] Already downloaded ({len(cached_images)} images)")
        result.images.extend(cached_images)
        return result

    print(f"  [{comic_name}] Fetching {url} ...")
    try:
        response = requests.get(url, headers=_HEADERS, timeout=30)
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, "html.parser")

        # Each comic lives in a div.tfs-comic container.
        # The image is lazy-loaded: real URL is in data-src, not src.
        # The caption (if any) is in a sibling <figure> within the same container.
        comics_found = []
        for container in soup.find_all("div", class_=_COMIC_CONTAINER_CLASS):
            img = container.find("img", attrs={"data-src": lambda s: s and _CDN_DOMAIN in s})
            if img:
                figcaption = container.find("figcaption")
                comics_found.append((img, figcaption))
            if len(comics_found) >= max_images:
                break

        if not comics_found:
            raise RuntimeError(
                f"No comic containers ({_COMIC_CONTAINER_CLASS!r}) with "
                f"{_CDN_DOMAIN} images found on the page"
            )

        # Save cache only on success
        (cache_dir / f"{comic_id}.html").write_text(html, encoding="utf-8")

        for i, (img, figcaption) in enumerate(comics_found):
            cid = slot_cid(i)
            image_path = images_dir / slot_filename(i)

            img_url = img.get("data-src", "")
            r = requests.get(img_url, headers=_HEADERS, timeout=30)
            r.raise_for_status()
            image_path.write_bytes(r.content)

            caption = ""
            if figcaption:
                # separator=" " prevents words adjacent to inline tags (e.g. <i>)
                # from being run together; re.sub collapses any remaining
                # internal newlines or multiple spaces into one.
                text = re.sub(r"\s+", " ", figcaption.get_text(separator=" ")).strip()
                if text:
                    caption = f"<h3>{text}</h3>"

            result.images.append(
                ImageResult(cid=cid, image_path=image_path, caption=caption)
            )
            print(f"  [{comic_name}] Downloaded image {i + 1}: {image_path.name}")

    except Exception as e:
        result.error = str(e)
        print(f"  [{comic_name}] ERROR: {e}")

    return result
