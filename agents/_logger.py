"""
Shared logger factory — private module (starts with _), not mapped as a route.
"""

import sys
from datetime import datetime, timezone


def _safe(text: str) -> str:
    """Make log text safe for GBK-based log pipes on some Windows runtimes.

    The EdgeOne local worker may capture stdout using the system default
    encoding (GBK on zh-CN Windows). Emoji/other non-GBK characters would
    raise UnicodeEncodeError and surface as a spurious error event, so
    escape anything the target encoding cannot represent.
    """
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
        return text
    except (UnicodeEncodeError, LookupError):
        return text.encode(encoding, errors="backslashreplace").decode(encoding)


def create_logger(tag: str):
    """Create a logger with the given tag prefix."""

    class _Logger:
        @staticmethod
        def _ts() -> str:
            return datetime.now(timezone.utc).isoformat()

        @staticmethod
        def log(*args: object) -> None:
            print(_safe(f"[{tag}][{_Logger._ts()}]"), *[_safe(str(a)) for a in args], flush=True)

        @staticmethod
        def error(*args: object) -> None:
            print(
                _safe(f"[{tag}][{_Logger._ts()}]"),
                *[_safe(str(a)) for a in args],
                file=sys.stderr,
                flush=True,
            )

    return _Logger()
