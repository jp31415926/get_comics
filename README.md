# Comics Emailer

Downloads daily comics from multiple sources and sends them as an inline-image
HTML email. If any comic fails to download, sends an error notification instead
and does not send the comics email.

## First Run / Setup

```bash
./run.sh
```

On first run this will:
1. Create a Python virtual environment (`venv/`)
2. Install Python dependencies
3. Download Chromium for Playwright

Subsequent runs just execute `main.py` inside the venv.

## Configuration

All settings are in `config.toml`. You should not need to edit any Python files
for routine maintenance.

### Email addresses

```toml
[email]
to_addr = "to@example.com"          # change to mailing list for production
errors_to = ["errors@example.com", "errors2@example.com"]
```

Keep `to_addr` set to your personal address while testing. Only switch it to
the announce-only mailing list for production runs.

### Adding a comic

Add a `[[comics]]` block in `config.toml`. The order of blocks determines the
order in the email. See `docs/adding-comics.md` for details.

### Changing image / cache directories

```toml
[paths]
images_dir = "images"
cache_dir = "last_known_good_cache"
```

Paths are relative to the project root.

## When a Comic Fails

1. Check the error notification email for the error message.
2. See `docs/troubleshooting.md` for a step-by-step guide.

## Scheduling

To run daily via cron (e.g. 6 AM):

```
0 6 * * * /home/jp/comics/run.sh >> /home/jp/comics/comics.log 2>&1
```
