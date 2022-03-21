"""
Defining and configuring the logger
"""

import logging
from sys import stderr, stdout
from threading import current_thread, main_thread

from .ansi import ansi_format

# from .constants import NAME


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
VERBOSE_INFO = logging.INFO - 2
VERBOSE_DEBUG = logging.DEBUG - 2
logging.addLevelName(VERBOSE_INFO, "VERBOSE_INFO")
logging.addLevelName(VERBOSE_DEBUG, "VERBOSE_DEBUG")

DEFAULT_LEVEL = logging.INFO


class Logger:

    logger: logging.Logger
    error_handler: logging.StreamHandler
    info_handler: logging.StreamHandler

    has_written: bool = False

    def __init__(self):
        # create logger
        self.logger = logging.root  # logging.getLogger(NAME)
        # Errors got to STDERR
        self.error_handler = logging.StreamHandler(stderr)
        self.error_handler.addFilter(LevelFilter(logging.WARN, logging.CRITICAL))
        self.error_handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(self.error_handler)
        # Everything else goes to STDOUT
        self.info_handler = logging.StreamHandler(stdout)
        self.info_handler.addFilter(LevelFilter(0, logging.WARN - 1))
        self.info_handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(self.info_handler)

        self.logger.setLevel(DEFAULT_LEVEL)

    @staticmethod
    def add_thread_info(message: str) -> str:
        """Add thread name to message if not in main thread"""
        current = current_thread()
        if current is not main_thread():
            message = "[{FgBlue}" + current.name + "{Reset}] " + message
        return message

    def to_logger(self, level: int, message: str, *args, **kwargs) -> None:
        """Formats a message (with given args and ansi colors)
        and sends it to the logger with the given level"""
        message = ansi_format(self.add_thread_info(message), *args, **kwargs)
        self.logger.log(level=level, msg=message)
        self.has_written = True

    def warn(self, message: str, *args, **kwargs) -> None:
        """Issue a warning, extra arguments are formatter options"""
        self.to_logger(
            logging.WARN, "{FgPurple}WARNING:{Reset} " + message, *args, **kwargs
        )

    def error(self, message: str, *args, **kwargs) -> None:
        """Issue an error, extra arguments are formatter options"""
        self.to_logger(
            logging.ERROR, "{FgRed}ERROR:{Reset} " + message, *args, **kwargs
        )

    def critical(self, message: str, *args, **kwargs) -> None:
        """Issue a critical error, extra arguments are formatter options"""
        self.to_logger(
            logging.CRITICAL,
            "{FgRed}CRITICAL ERROR:{Reset} " + message,
            *args,
            **kwargs
        )

    def info(self, message: str, *args, **kwargs) -> None:
        """Show info, extra arguments are formatter options"""
        self.to_logger(logging.INFO, message, *args, **kwargs)

    def verbose_info(self, message: str, *args, **kwargs) -> None:
        """Show info when verbose, extra arguments are formatter options"""
        self.to_logger(VERBOSE_INFO, message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs) -> None:
        """Show debug info, extra arguments are formatter options"""
        self.to_logger(logging.DEBUG, message, *args, **kwargs)

    def verbose_debug(self, message: str, *args, **kwargs) -> None:
        """Show very verbose debug info, extra arguments are formatter options"""
        self.to_logger(VERBOSE_DEBUG, message, *args, **kwargs)

    def set_level(self, level: int) -> None:
        """Set the logger's level, using logging's level values"""
        self.logger.setLevel(level)

    verbosity = {
        -4: logging.CRITICAL + 10,
        -3: logging.CRITICAL,
        -2: logging.ERROR,
        -1: logging.WARN,
        0: logging.INFO,
        1: VERBOSE_INFO,
        2: logging.DEBUG,
        3: VERBOSE_DEBUG,
    }

    def set_verbosity(self, verbosity: int) -> None:
        """Set verbosity:
        0 is default
        1, 2, 3 show more and more info
        -1, -2, -3, -4 show less and less (warning, error, critical errors, then nothing)"""
        maxi = max(self.verbosity)
        mini = min(self.verbosity)
        if verbosity > maxi:
            verbosity = maxi
        if verbosity < mini:
            verbosity = mini
        self.set_level(self.verbosity[verbosity])

    def header(self, title: str, level: int = logging.INFO) -> None:
        """Shows a pretty header, 100% inspired by opam's output"""
        self.to_logger(level, "")  # newline
        title = (
            "{FgBlue}===={Reset} {StBold}"
            + title
            + "{Reset} {FgBlue}"
            + ("=" * (74 - len(title)))
            + "{Reset}"
        )
        self.to_logger(level, title)


logger = Logger()
