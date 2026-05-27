import os
from pathlib import Path
import tomllib

CONFIG_PATH = Path(os.environ.get("PLACEHOLDER_KEYWORDS_FILE", "/app/config/placeholder_keywords.toml"))


def load_keyword_config(path: Path = CONFIG_PATH) -> dict[str, list[str]]:
    with path.open("rb") as f:
        config = tomllib.load(f)

    return {
        "placeholder_keywords": list(dict.fromkeys(config["placeholder_keywords"])),
        "version_placeholder_keywords": list(dict.fromkeys(config["version_placeholder_keywords"])),
        "function_keywords": list(dict.fromkeys(config["function_keywords"])),
    }
