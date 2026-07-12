from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ImageResult:
    """A single downloaded comic image."""
    cid: str         # Content-ID used for inline email embedding (e.g. "tfs", "tfs2")
    image_path: Path
    caption: str = ""  # Optional HTML string (used by The Far Side)


@dataclass
class ComicResult:
    """Result of attempting to download one comic.

    Most comics produce one ImageResult. The Far Side produces two.
    Check .success before using .images.
    """
    comic_id: str
    comic_name: str
    page_url: str
    images: list[ImageResult] = field(default_factory=list)
    error: str = ""

    @property
    def success(self) -> bool:
        return bool(self.images) and not self.error
