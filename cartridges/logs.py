# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Optional debug log files, rotated by size, in the user's state directory."""

import logging
import logging.handlers
import platform
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import override

from gi.repository import GLib

from . import STATE_DIR
from .config import APP_ID, VERSION

LOG_DIR: Path = STATE_DIR / "logs"
MAX_BYTES: int = 1_048_576
BACKUP_COUNT: int = 4

# Pillow logs every chunk of every image it reads at the debug level.
_NOISY_LOGGERS = ("PIL",)

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_REDACTED = "[redacted]"
_MIN_SECRET_LENGTH = 8

_logger = logging.getLogger(__name__)

_handler: "_LogFileHandler | None" = None
_previous_root_level: int = logging.INFO
_secret: str = ""

_failure_callback: Callable[[], None] | None = None
_failure_reported: bool = False
_failure_pending: bool = False


class _LogFileHandler(logging.handlers.RotatingFileHandler):
    """A rotating file handler that redacts secrets and never raises on failure."""

    def __init__(self, filename: Path, max_bytes: int, backup_count: int) -> None:
        super().__init__(
            filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
            delay=True,
        )
        self.setFormatter(logging.Formatter(_FORMAT))
        self._failed = False

    @override
    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        if len(_secret) >= _MIN_SECRET_LENGTH:
            text = text.replace(_secret, _REDACTED)
        return text

    @override
    def emit(self, record: logging.LogRecord) -> None:
        if self._failed:
            return

        # Start a new file if the current one was removed while open.
        if self.stream is not None and not Path(self.baseFilename).exists():
            self.stream.close()
            self.stream = None  # pyright: ignore[reportAttributeAccessIssue]

        super().emit(record)

    @override
    def handleError(self, record: logging.LogRecord) -> None:
        # Stop writing for the rest of the run instead of printing a traceback
        # for every record, and tell the user once.
        self._failed = True
        _report_failure()
        GLib.idle_add(_disable_handler, self)


def log_file(directory: Path = LOG_DIR) -> Path:
    """Get the path of the current log file in `directory`."""
    return directory / f"{APP_ID}.log"


def set_secret(secret: str) -> None:
    """Set a value that must never be written to the log files."""
    global _secret  # noqa: PLW0603
    _secret = secret


def set_failure_callback(callback: Callable[[], None]) -> None:
    """Set the function called on the main loop, once per run, when logs fail."""
    global _failure_callback, _failure_pending  # noqa: PLW0603
    _failure_callback = callback
    if _failure_pending:
        _failure_pending = False
        GLib.idle_add(_call_failure_callback)


def enable(
    directory: Path = LOG_DIR,
    max_bytes: int = MAX_BYTES,
    backup_count: int = BACKUP_COUNT,
) -> bool:
    """Start writing debug logs to `directory`.

    Returns whether logging is on. Does nothing if it already is.
    """
    global _handler, _previous_root_level  # noqa: PLW0603

    if _handler is not None:
        return True

    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        _report_failure()
        return False

    root = logging.getLogger()

    # Keep existing handlers, such as the terminal, at their current output.
    for existing in root.handlers:
        if existing.level == logging.NOTSET:
            existing.setLevel(logging.INFO)

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.INFO)

    _handler = _LogFileHandler(log_file(directory), max_bytes, backup_count)
    _handler.setLevel(logging.DEBUG)
    root.addHandler(_handler)

    _previous_root_level = root.level
    root.setLevel(logging.DEBUG)

    # Write the header only to the file, not to the terminal.
    _handler.handle(
        _logger.makeRecord(_logger.name, logging.INFO, __file__, 0, _header(), (), None)
    )
    return True


def disable() -> None:
    """Stop writing debug logs. Existing files are kept."""
    global _handler  # noqa: PLW0603

    if _handler is None:
        return

    root = logging.getLogger()
    root.removeHandler(_handler)
    root.setLevel(_previous_root_level)
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.NOTSET)
    _handler.close()
    _handler = None


def install_exception_hooks() -> None:
    """Write unhandled exceptions to the debug log, then run the previous hook.

    Python reports them on stderr only. The record goes to the file handler alone
    so the terminal output stays as it was.
    """
    previous_except = sys.excepthook
    previous_thread = threading.excepthook
    previous_unraisable = sys.unraisablehook

    # `sys.UnraisableHookArgs` exists only in the type stubs, so it is quoted.

    def log_exception(message: str, exc_value: BaseException | None) -> None:
        if _handler is not None and exc_value is not None:
            _handler.handle(
                _logger.makeRecord(
                    _logger.name,
                    logging.CRITICAL,
                    __file__,
                    0,
                    message,
                    (),
                    (type(exc_value), exc_value, exc_value.__traceback__),
                )
            )

    def except_hook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        log_exception("Unhandled exception", exc_value)
        previous_except(exc_type, exc_value, exc_traceback)

    def thread_hook(args: threading.ExceptHookArgs) -> None:
        if args.exc_type is not SystemExit:
            log_exception("Unhandled exception in thread", args.exc_value)
        previous_thread(args)

    def unraisable_hook(args: "sys.UnraisableHookArgs") -> None:
        log_exception("Unraisable exception", args.exc_value)
        previous_unraisable(args)

    sys.excepthook = except_hook
    threading.excepthook = thread_hook
    sys.unraisablehook = unraisable_hook


def setup() -> None:
    """Apply the debug logs setting and follow its changes."""
    from gi.repository import Gio

    from . import SETTINGS

    def on_debug_logs_changed(settings: Gio.Settings, key: str) -> None:
        if settings.get_boolean(key):
            enable()
        else:
            disable()

    def on_secret_changed(settings: Gio.Settings, key: str) -> None:
        set_secret(settings.get_string(key).strip())

    install_exception_hooks()
    on_secret_changed(SETTINGS, "sgdb-key")
    on_debug_logs_changed(SETTINGS, "debug-logs")
    SETTINGS.connect("changed::sgdb-key", on_secret_changed)
    SETTINGS.connect("changed::debug-logs", on_debug_logs_changed)


def _header() -> str:
    from gi.repository import Adw, Gtk

    flatpak = "yes" if Path("/.flatpak-info").exists() else "no"
    gtk = ".".join(
        map(
            str,
            (
                Gtk.get_major_version(),
                Gtk.get_minor_version(),
                Gtk.get_micro_version(),
            ),
        )
    )
    adw = ".".join(
        map(
            str,
            (
                Adw.get_major_version(),
                Adw.get_minor_version(),
                Adw.get_micro_version(),
            ),
        )
    )
    return (
        f"Cartridges {VERSION} {APP_ID}, flatpak={flatpak}, "
        f"Python {platform.python_version()}, GTK {gtk}, Adwaita {adw}, "
        f"{sys.platform}"
    )


def _disable_handler(handler: _LogFileHandler) -> bool:
    if handler is _handler:
        disable()
    return GLib.SOURCE_REMOVE


def _report_failure() -> None:
    global _failure_reported, _failure_pending  # noqa: PLW0603

    if _failure_reported:
        return
    _failure_reported = True

    if _failure_callback is None:
        _failure_pending = True
    else:
        GLib.idle_add(_call_failure_callback)


def _call_failure_callback() -> bool:
    if _failure_callback is not None:
        _failure_callback()
    return GLib.SOURCE_REMOVE
