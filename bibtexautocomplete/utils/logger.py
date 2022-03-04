"""
Defining and configuring the logger
"""

import logging
from sys import stderr, stdout

from .constants import NAME


class LevelFilter(logging.Filter):
    def __init__(self, low, high):
        self._low = low
        self._high = high
        logging.Filter.__init__(self)

    def filter(self, record):
        if self._low <= record.levelno <= self._high:
            return True
        return False


# custom level
PROGRESS = logging.INFO + 2
DEBUGLOW = logging.DEBUG - 2
logging.addLevelName(PROGRESS, "PROGRESS")
logging.addLevelName(DEBUGLOW, "DEBUGLOW")

DEFAULT_LEVEL = PROGRESS

# create logger
logger = logging.getLogger(NAME)
error_handler = logging.StreamHandler(stderr)
error_handler.addFilter(LevelFilter(logging.WARN, logging.CRITICAL))
error_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
logger.addHandler(error_handler)
info_handler = logging.StreamHandler(stdout)
info_handler.addFilter(LevelFilter(0, logging.WARN - 1))
logger.addHandler(info_handler)


def set_logger_level(level: int) -> None:
    """Translate my program levels into logger levels
    -1 = silent => logging.ERROR
    0 = default => PROGRESS
    1 = verbose => logging.INFO
    2 = very verbose => logging.DEBUG
    3 = very very verbose => DEBUGLOW"""
    if level < 0:
        formatter_str = "%(message)s"
        logger.setLevel(logging.ERROR)
    elif level == 0:
        formatter_str = "%(message)s"
        logger.setLevel(PROGRESS)
    elif level == 1:
        formatter_str = "%(asctime)s - %(message)s"
        logger.setLevel(logging.INFO)
    elif level == 2:
        formatter_str = "%(asctime)s - %(levelname)s - %(message)s"
        logger.setLevel(logging.DEBUG)
    else:
        formatter_str = "%(asctime)s - %(levelname)s - %(message)s"
        logger.setLevel(DEBUGLOW)
    formatter = logging.Formatter(
        formatter_str,
        datefmt="%H:%M:%S",
    )
    info_handler.setFormatter(formatter)


set_logger_level(0)
