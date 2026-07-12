import tomllib
from pathlib import Path

_BASE_DIR = Path(__file__).parent.parent


def load_config(config_path: Path = None) -> dict:
    if config_path is None:
        config_path = _BASE_DIR / "config.toml"
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def get_images_dir(config: dict) -> Path:
    return _BASE_DIR / config["paths"]["images_dir"]


def get_cache_dir(config: dict) -> Path:
    return _BASE_DIR / config["paths"]["cache_dir"]
