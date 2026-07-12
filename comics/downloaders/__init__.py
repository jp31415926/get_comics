from .arcamax import download_arcamax
from .creators import download_creators
from .thefarside import download_thefarside
from .xkcd import download_xkcd

# gocomics is handled separately in main.py — it needs a shared Playwright page object.
# All other downloaders use requests and are registered here.
DOWNLOADERS = {
    "arcamax": download_arcamax,
    "creators": download_creators,
    "thefarside": download_thefarside,
    "xkcd": download_xkcd,
}
