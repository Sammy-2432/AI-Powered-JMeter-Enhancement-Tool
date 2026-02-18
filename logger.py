from loguru import logger
from pathlib import Path


def setup_logger(name: str = "app"):
    Path("temp/logs").mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add("temp/logs/app.log", rotation="10 MB", retention="10 days")
    return logger
