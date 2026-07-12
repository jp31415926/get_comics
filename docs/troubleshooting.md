# Troubleshooting

## A comic failed — where do I look?

Each downloader file is named after the site it handles. When a specific comic
fails, check the file for that comic's source:

| Comic | Source | Downloader file |
|-------|--------|----------------|
| Loose Parts | gocomics.com | `comics/downloaders/gocomics.py` |
| Calvin and Hobbes | gocomics.com | `comics/downloaders/gocomics.py` |
| Off the Mark | gocomics.com | `comics/downloaders/gocomics.py` |
| F Minus | gocomics.com | `comics/downloaders/gocomics.py` |
| Daddy's Home | gocomics.com | `comics/downloaders/gocomics.py` |
| The Far Side | thefarside.com | `comics/downloaders/thefarside.py` |
| B.C. | arcamax.com | `comics/downloaders/arcamax.py` |
| Bizarro | arcamax.com | `comics/downloaders/arcamax.py` |
| Jerry King Cartoons | arcamax.com | `comics/downloaders/arcamax.py` |
| The Fortune Teller | arcamax.com | `comics/downloaders/arcamax.py` |
| xkcd | xkcd.com | `comics/downloaders/xkcd.py` |
| Wizard of Id | creators.com | `comics/downloaders/creators.py` |

The docstring at the top of each file describes exactly what HTML element or
attribute the downloader looks for.

---

## gocomics.com: selector stopped working

This is the most common failure. gocomics.com uses React with CSS Modules, and
class names like `Comic_comic__image__abc123` change every time they redeploy.

**Symptoms:** Error message contains "Comic image not found with primary selector".
Debug files are saved automatically:
- `images/{comic_id}_debug.png` — screenshot of the page at failure time
- `last_known_good_cache/{comic_id}_debug.html` — full page HTML at failure time

**Fix:**
1. Open the debug HTML or screenshot to inspect the current page structure.
2. Compare with `last_known_good_cache/{comic_id}.html` (the last working version)
   to see what changed.
3. Find the new CSS selector for the comic image (look for the `<img>` inside
   the main comic container).
4. Update the `selector` value in `config.toml` for the failing comic(s).
   All gocomics.com comics share the same class naming scheme, so they usually
   all break together and need the same fix.

**Automatic fallbacks:** Before giving up, the downloader also tries these
selectors automatically (defined in `comics/downloaders/gocomics.py`):
```python
FALLBACK_SELECTORS = [
    'picture img[src*="featureassets"]',
    'img[src*="featureassets.gocomics.com"]',
    '[class*="Comic"] img[src*="featureassets"]',
    'article img[src*="featureassets"]',
]
```
The CDN domain `featureassets.gocomics.com` has been stable. If any fallback
matches, a note is printed to the log indicating which one worked, so you can
update `config.toml` to use it as the new primary selector.

---

## arcamax.com: image not found

The downloader looks for `<img data-zoom-image="...">`. If that attribute has
been renamed, compare `last_known_good_cache/{comic_id}.html` against the
current page source and find the new attribute or element that holds the
full-resolution image URL.

---

## The Far Side: images not found

The downloader searches for `<figure>` elements containing an `<img>` whose
`src` points to `assets.amuniversal.com`. If that fails, check whether:
- The CDN domain changed (update `_CDN_DOMAIN` in `thefarside.py`)
- The page structure no longer uses `<figure>` elements (update the search logic)

Compare `last_known_good_cache/tfs.html` against the current page.

---

## xkcd: image not found

Looks for `<div id="comic"><img>`. xkcd's structure has been stable for many
years, but if it changes, compare `last_known_good_cache/xkcd.html` against
the current page.

---

## Wizard of Id: image not found

Uses the `<meta property="og:image">` Open Graph tag. If the tag is missing,
creators.com may have changed their meta tag structure. Compare
`last_known_good_cache/wiz.html` against the current page.

---

## Comparing last-known-good vs current

A useful pattern when debugging any failure:

```bash
# Fetch current page source
curl -A "Mozilla/5.0" https://www.example.com/comic > /tmp/current.html

# Diff against last working version
diff last_known_good_cache/{comic_id}.html /tmp/current.html | less
```

Look for changes near the image element or its container.

---

## Running manually

```bash
./run.sh
```

Output goes to stdout. Add a date stamp for log files:

```bash
./run.sh 2>&1 | tee -a comics.log
```
