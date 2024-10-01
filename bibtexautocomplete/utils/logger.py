"""
Defining and configuring the logger
"""

import logging
from sys import stderr, stdout, version
from threading import current_thread, main_thread
from traceback import format_exc

from .ansi import ansi_format, ansiless_len
from .constants import ISSUES_URL, NAME, VERSION_DATE, VERSION_STR

Level = int


class LevelFilter(logging.Filter):
    def __init__(self, low: Level, high: Level):
        self._low = low
        self._high = high
        logging.Filter.__init__(self)

    def filter(self, record: logging.LogRecord) -> bool:
        if self._low <= record.levelno <= self._high:
            return True
        return False


# custom level
VERBOSE_INFO = logging.INFO - 2
VERBOSE_DEBUG = logging.DEBUG - 2
VERY_VERBOSE_DEBUG = VERBOSE_DEBUG - 2
logging.addLevelName(VERBOSE_INFO, "VERBOSE_INFO")
logging.addLevelName(VERBOSE_DEBUG, "VERBOSE_DEBUG")
logging.addLevelName(VERY_VERBOSE_DEBUG, "VERY_VERBOSE_DEBUG")

DEFAULT_LEVEL = logging.INFO


def prefix_indent(prefix: str, message: str) -> str:
    """Adds a prefix to the first line of message
    Indents all subsequent lines with spaces to be aligned to prefix"""
    len = ansiless_len(prefix)
    return ansi_format(prefix) + message.replace("\n", "\n" + " " * len)


class Logger:
    logger: logging.Logger

    def __init__(self, logger_name: str) -> None:
        # create logger
        self.logger = logging.getLogger(logger_name)
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
            info = "[{FgBlue}" + current.name + "{Reset}] "
            entry_name = current.entry_name if hasattr(current, "entry_name") else None
            if isinstance(entry_name, str):
                info += "{StUnderline}" + entry_name + ":{Reset} "
            message = prefix_indent(info, message)
        return message

    def to_logger(self, level: int, message: str, *args: object, **kwargs: object) -> None:
        """Formats a message (with given args and ansi colors)
        and sends it to the logger with the given level"""
        message = self.add_thread_info(ansi_format(message, *args, **kwargs))
        self.logger.log(level=level, msg=message)

    def warn(self, message: str, error: str = "WARNING", *args: object, **kwargs: object) -> None:
        """Issue a warning, extra arguments are formatter options"""
        self.to_logger(
            logging.WARN,
            "{FgPurple}{error}:{Reset} " + message,
            *args,
            error=error,
            **kwargs,
        )

    def error(self, message: str, error: str = "ERROR", *args: object, **kwargs: object) -> None:
        """Issue an error, extra arguments are formatter options"""
        self.to_logger(
            logging.ERROR,
            "{FgRed}{error}:{Reset} " + message,
            *args,
            error=error,
            **kwargs,
        )

    def critical(self, message: str, error: str = "CRITICAL ERROR", *args: object, **kwargs: object) -> None:
        """Issue a critical error, extra arguments are formatter options"""
        self.to_logger(
            logging.CRITICAL,
            "{FgRed}{error}:{Reset} " + message,
            *args,
            error=error,
            **kwargs,
        )

    def info(self, message: str, *args: object, **kwargs: object) -> None:
        """Show info, extra arguments are formatter options"""
        self.to_logger(logging.INFO, message, *args, **kwargs)

    def verbose_info(self, message: str, *args: object, **kwargs: object) -> None:
        """Show info when verbose, extra arguments are formatter options"""
        self.to_logger(VERBOSE_INFO, message, *args, **kwargs)

    def debug(self, message: str, *args: object, **kwargs: object) -> None:
        """Show debug info, extra arguments are formatter options"""
        self.to_logger(logging.DEBUG, message, *args, **kwargs)

    def verbose_debug(self, message: str, *args: object, **kwargs: object) -> None:
        """Show verbose debug info, extra arguments are formatter options"""
        self.to_logger(VERBOSE_DEBUG, message, *args, **kwargs)

    def very_verbose_debug(self, message: str, *args: object, **kwargs: object) -> None:
        """Show very verbose debug info, extra arguments are formatter options"""
        self.to_logger(VERY_VERBOSE_DEBUG, message, *args, **kwargs)

    def forget(self, message: str, *args: object, **kwargs: object) -> None:
        """Forgets info passed to it"""
        pass

    def set_level(self, level: Level) -> None:
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
        4: VERY_VERBOSE_DEBUG,
    }

    def set_verbosity(self, verbosity: int) -> None:
        """Set verbosity:
        0 is default
        1, 2, 3 show more and more info
        -1, -2, -3, -4 show less and less (warning, error, critical errors, then nothing)
        """
        maxi = max(self.verbosity)
        mini = min(self.verbosity)
        if verbosity > maxi:
            verbosity = maxi
        if verbosity < mini:
            verbosity = mini
        self.set_level(self.verbosity[verbosity])

    def get_level(self) -> int:
        """Returns the logger level"""
        return self.logger.getEffectiveLevel()

    def header(self, title: str, level: Level = logging.INFO) -> None:
        """Shows a pretty header, 100% inspired by opam's output"""
        self.to_logger(level, "")  # newline
        title = "{FgBlue}===={Reset} {StBold}" + title + "{Reset} {FgBlue}" + ("=" * (74 - len(title))) + "{Reset}"
        self.to_logger(level, title)

    def traceback(self, message: str, _err: Exception) -> None:
        prefix = ansi_format("{FgRed} | {Reset}")
        message = message.replace("\n", "\n" + prefix)
        m = message.split("\n")
        # Hack to ensure second line is erased
        if len(m):
            m[0] = m[0].ljust(80)
            message = "\n".join(m)
        self.error(
            "\n"
            + prefix
            + "{tmessage}\n"
            + prefix
            + "\n"
            + prefix
            + "{FgRed}{exn}{FgReset}\n"
            + prefix
            + "\n"
            + prefix
            + "{StBold}You can report this bug at {StUnderline}{ISSUES_URL}{Reset}{StBold}.{Reset}\n"
            + prefix
            + "{StBold}Please include the above traceback and the offending entry in your report.{Reset}\n"
            + prefix
            + "BTAC: {BTAC_VERSION}, Python: {PYTHON_VERSION}\n"
            + prefix,
            error="UNEXPECTED ERROR",
            tmessage=message,
            ISSUES_URL=ISSUES_URL,
            BTAC_VERSION=VERSION_STR + " " + VERSION_DATE,
            PYTHON_VERSION=version,
            exn=format_exc().strip().replace("\n", "\n" + prefix + ansi_format("{FgRed}")),
        )


logger = Logger(NAME)


class Hint:
    """Hints are messages displayed only once"""

    prefix = "{FgBlue}Hint:{Reset} "
    indent = " " * 6

    emitted: bool
    message: str

    def __init__(self, message: str) -> None:
        self.message = self.prefix + message.strip().replace("\n", self.indent + "\n")
        self.emitted = False

    def emit(self) -> None:
        if not self.emitted:
            self.emitted = True
            logger.info(self.message)
