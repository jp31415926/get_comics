#!/usr/bin/env python3
"""
Comic downloader and emailer.

Downloads comics from multiple sources and sends them as an inline-image
HTML email. If any comic fails to download, sends an error notification
instead and exits without sending the comics email.

Run via:  ./run.sh
"""

import asyncio
import sys

from playwright.async_api import async_playwright

from comics.config import load_config, get_images_dir, get_cache_dir
from comics.downloaders import DOWNLOADERS
from comics.downloaders.gocomics import download_gocomic
from comics.email_sender import send_comics_email, send_error_email

# Injected into every Playwright page to reduce bot-detection signals
_STEALTH_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    window.chrome = {runtime: {}, loadTimes: () => ({})};
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications'
            ? Promise.resolve({state: Notification.permission})
            : originalQuery(parameters)
    );
    Object.defineProperty(navigator, 'userAgentData', {
        get: () => ({
            brands: [
                {brand: 'Google Chrome', version: '116'},
                {brand: 'Chromium', version: '116'},
                {brand: ';Not A Brand', version: '99'},
            ],
            mobile: false,
            platform: 'Windows',
        })
    });
"""


async def run() -> None:
    config = load_config()
    images_dir = get_images_dir(config)
    cache_dir = get_cache_dir(config)

    images_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    comics = config["comics"]
    gocomics_entries = [c for c in comics if c["downloader"] == "gocomics"]
    simple_entries = [c for c in comics if c["downloader"] != "gocomics"]

    results_by_id = {}

    # --- Playwright comics (one shared browser session) ---
    if gocomics_entries:
        print("\n=== gocomics.com (Playwright) ===")
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            context = await browser.new_context(
                viewport={"width": 1400, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/116.0.0.0 Safari/537.36"
                ),
                locale="en-US",
            )
            page = await context.new_page()
            await page.add_init_script(_STEALTH_SCRIPT)

            for comic in gocomics_entries:
                result = await download_gocomic(
                    comic, images_dir, cache_dir, page=page
                )
                results_by_id[comic["id"]] = result

            await browser.close()

    # --- Simple (requests-based) comics ---
    if simple_entries:
        print("\n=== Other sources (requests) ===")
        for comic in simple_entries:
            downloader = DOWNLOADERS[comic["downloader"]]
            result = await downloader(comic, images_dir, cache_dir)
            results_by_id[comic["id"]] = result

    # Reconstruct results in config order (determines email order)
    results = [results_by_id[c["id"]] for c in comics]

    # --- Report and decide ---
    failures = [(r.comic_name, r.error) for r in results if not r.success]

    print()
    if failures:
        print(f"FAILED ({len(failures)} comic(s)):")
        for name, error in failures:
            print(f"  - {name}: {error}")
        send_error_email(failures, config)
        sys.exit(1)

    print(f"All {len(results)} comics downloaded successfully.")
    send_comics_email(results, config)


if __name__ == "__main__":
    asyncio.run(run())
