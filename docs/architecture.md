# Architecture

## Project Structure

```
comics/
  config.toml                   — all settings and comic definitions
  main.py                       — entry point
  run.sh                        — venv setup + runner (use this to invoke the script)
  requirements.txt
  README.md
  docs/                         — this directory
  comics/                       — Python package
    config.py                   — config loading helpers
    email_sender.py             — builds and sends the MIME email
    downloaders/
      base.py                   — ComicResult and ImageResult dataclasses
      gocomics.py               — Playwright-based (gocomics.com)
      thefarside.py             — requests + BeautifulSoup (thefarside.com)
      arcamax.py                — requests + BeautifulSoup (arcamax.com)
      xkcd.py                   — requests + BeautifulSoup (xkcd.com)
      creators.py               — requests + BeautifulSoup (creators.com)
  images/                       — downloaded images (prefix-YYYYMMDD.ext)
  last_known_good_cache/        — last successful raw HTML per comic
```

## Why Two Download Strategies?

**gocomics.com** uses a JavaScript-heavy React frontend. The comic image is not
present in the raw HTML — it is rendered by JavaScript after page load.
Playwright controls a real Chromium browser to handle this.

All other sources return the image URL in the raw HTML and can be fetched with
a plain HTTP request + BeautifulSoup for parsing.

If other sources eventually move to JavaScript-rendered pages, change their
`downloader` value in `config.toml` to `gocomics` and add a `selector` line.

## Playwright Browser Session

A single Chromium browser is opened once, and all gocomics.com comics are
downloaded sequentially through the same page object. This avoids the overhead
of launching a browser per comic. The browser is closed when all gocomics
downloads are complete.

## Data Flow

```
config.toml
    │
    ▼
main.py  ──► opens Playwright browser
    │              │
    │         gocomics.py (for each gocomics comic)
    │              │
    ├──────────────┘
    │
    ├──► thefarside.py
    ├──► arcamax.py      (for each arcamax comic)
    ├──► xkcd.py
    └──► creators.py
              │
              ▼
         results[]  (ComicResult objects, in config order)
              │
      ┌───────┴───────┐
   all ok?          any failed?
      │                  │
      ▼                  ▼
 comics email       error email
 (to_addr)         (errors_to)
```

## Email Format

The email is `multipart/related` with:
- One `text/html` part containing inline `<img src="cid:...">` references
- One `image/*` attachment per comic image, with a matching `Content-ID` header

The From address (`jp_gkbs3wqbtrqpztqbnuwliwv2kptmlrgasfy8m7jr4nm@gcfl.net`)
is required to post to the announce-only mailing list. Do not change it.

## Cache Files

`last_known_good_cache/{comic_id}.html` is written **only when a download
succeeds**. This means it always contains the HTML from the last working run.
When a comic breaks, you can compare this file against the current live page to
see what changed. See `docs/troubleshooting.md`.
