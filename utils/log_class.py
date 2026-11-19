'''function for common tasks'''
from pathlib import Path
from loguru import logger
import yaml

ENCODING = "utf-8"

_CONFIGURED = False
DEFAULT_CONFIG = Path(__file__).parent / "configPoC.yaml"


def setup_logger(config_path: str = DEFAULT_CONFIG,
                 setting: str = "default") -> None:
    """Configure Loguru once."""
    # Redundant code and yaml review TODO
    global _CONFIGURED

    if _CONFIGURED:
        return

    logger.remove()

    with open(config_path, encoding=ENCODING) as f:
        cfg = yaml.safe_load(f)["logger"]

    log_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level:<8} | "
        "{extra[module]} | "
        "{extra[file]} | "
        "{function}:{line} | "
        "{message}"
        )

    def severity_level_filter(number: int):
        """get only logs to a certain log level."""
        def _filter(record):
            return record["level"].no <= number
        return _filter

    Path("logs").mkdir(exist_ok=True)
    logger.add(**{k: v for k, v in cfg[setting].items() if k != "severity"},
               format=log_format,
               filter=severity_level_filter(cfg[setting]["severity"]))
    logger.add(**cfg["warning"], format=log_format)

    _CONFIGURED = True


def get_logger(module: str, file: str):
    """Example:
    from logging_utils import get_logger

    log = get_logger(__name__, __file__)

    log.info("Reading CSAF document")
        """
    setup_logger()  # ensure configuration is loaded
    return logger.bind(
        module=module,
        file=Path(file).name,
    )
