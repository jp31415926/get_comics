# Adding and Configuring Comics

## Adding a Comic

Add a `[[comics]]` block to `config.toml`. Comics appear in the email in the
same order as they appear in the file.

### Required fields for all comics

| Field        | Description |
|--------------|-------------|
| `id`         | Short unique identifier (used for CIDs, cache filenames, and debug output) |
| `name`       | Display name used in the email `<h2>` heading |
| `downloader` | Which downloader to use (see table below) |
| `url`        | The page URL to fetch |
| `prefix`     | Filename prefix — image saved as `{prefix}-YYYYMMDD.{extension}` |
| `extension`  | File extension: `gif`, `jpg`, or `png` |

### Downloader options

| Value        | Used for | How it finds the image |
|--------------|----------|------------------------|
| `gocomics`   | gocomics.com | CSS selector (Playwright, requires `selector` field) |
| `thefarside` | thefarside.com | `<figure>` → `<img src="assets.amuniversal.com/...">` |
| `arcamax`    | arcamax.com | `<img data-zoom-image="...">` |
| `xkcd`       | xkcd.com | `<div id="comic"> <img>` |
| `creators`   | creators.com | `<meta property="og:image">` |

### gocomics-specific fields

| Field      | Description |
|------------|-------------|
| `selector` | CSS selector for the comic image element. Updated here when it breaks — no code change needed. |

Example:
```toml
[[comics]]
id = "ph"
name = "Pearls Before Swine"
downloader = "gocomics"
url = "https://www.gocomics.com/pearlsbeforeswine"
prefix = "ph"
extension = "gif"
selector = 'img[class*="Comic_comic__image"]'
```

### thefarside-specific fields

| Field        | Default | Description |
|--------------|---------|-------------|
| `max_images` | 2       | Maximum number of comics to grab per day |

### Adding a site that needs a new downloader

If the site doesn't fit an existing downloader:
1. Create `comics/downloaders/{sitename}.py` following the pattern of an
   existing simple downloader (e.g. `arcamax.py`).
2. Register it in `comics/downloaders/__init__.py`.
3. Add the comic to `config.toml` with the new `downloader` value.

If the site requires JavaScript rendering, use the `gocomics` downloader as a
template and add a `selector` field to the config entry.

## Removing a Comic

Delete or comment out the corresponding `[[comics]]` block in `config.toml`.

## Reordering Comics

Move `[[comics]]` blocks in `config.toml`. The email reflects the file order.
