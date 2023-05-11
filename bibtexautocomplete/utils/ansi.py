"""
ANSI escape sequence for colors and styles
"""

from typing import Any


class ANSICodes:
    use_ansi: bool = True

    Codes = {
        # Foreground Colors
        "FgBlack": "\x1b[30m",
        "FgRed": "\x1b[31m",
        "FgGreen": "\x1b[32m",
        "FgYellow": "\x1b[33m",
        "FgBlue": "\x1b[34m",
        "FgPurple": "\x1b[35m",
        "FgCyan": "\x1b[36m",
        "FgWhite": "\x1b[37m",
        # Foreground Highlight Colors
        "FgHBlack": "\x1b[90m",
        "FgHRed": "\x1b[91m",
        "FgHGreen": "\x1b[92m",
        "FgHYellow": "\x1b[93m",
        "FgHBlue": "\x1b[94m",
        "FgHPurple": "\x1b[95m",
        "FgHCyan": "\x1b[96m",
        "FgHWhite": "\x1b[97m",
        "FgReset": "\x1b[38m",
        # Background Colors
        "BgBlack": "\x1b[40m",
        "BgRed": "\x1b[41m",
        "BgGreen": "\x1b[42m",
        "BgYellow": "\x1b[43m",
        "BgBlue": "\x1b[44m",
        "BgPurple": "\x1b[45m",
        "BgCyan": "\x1b[46m",
        "BgWhite": "\x1b[47m",
        # Background Highlight Colors
        "BgHBlack": "\x1b[100m",
        "BgHRed": "\x1b[101m",
        "BgHGreen": "\x1b[102m",
        "BgHYellow": "\x1b[103m",
        "BgHBlue": "\x1b[104m",
        "BgHPurple": "\x1b[105m",
        "BgHCyan": "\x1b[106m",
        "BgHWhite": "\x1b[107m",
        "BgReset": "\x1b[48m",
        # Styles
        "StBold": "\x1b[1m",
        "StBoldOff": "\x1b[22m",
        "StFaint": "\x1b[2m",
        "StFaintOff": "\x1b[22m",
        "StItalics": "\x1b[3m",
        "StItalicsOff": "\x1b[23m",
        "StUnderline": "\x1b[4m",
        "StUnderlineOff": "\x1b[24m",
        "StBlink": "\x1b[5m",
        "StBlinkOff": "\x1b[25m",
        "StInverse": "\x1b[7m",
        "StInverseOff": "\x1b[0m",
        "StBarred": "\x1b[9m",
        "StBarredOff": "\x1b[29m",
        "StOverline": "\x1b[53m",
        "StOverlineOff": "\x1b[55m",
        # Extras
        "Reset": "\x1b[0m",
        "Clearscreen": "\x1bc",
        "Clearline": "\x1b[2K\x1b[1G",
    }

    # Empty dict used when disabled
    EmptyCodes = {attr: "" for attr in Codes}

    @classmethod
    def ansi_format(cls, string: str, *args: Any, **kwargs: Any) -> str:
        """Return the string formatted with args and kwargs,
        adding the color formatters"""
        codes = cls.Codes
        if not cls.use_ansi:
            codes = cls.EmptyCodes
        return string.format(*args, **kwargs, **codes)

    @classmethod
    def ansiless_len(cls, string: str) -> int:
        """Length of a string without counting ANSI sequences"""
        codes = cls.EmptyCodes
        return len(string.format(**codes))


ansi_format = ANSICodes.ansi_format
ansiless_len = ANSICodes.ansiless_len
