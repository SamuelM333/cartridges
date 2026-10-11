# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Test writing, rotating, and redacting the optional debug log files."""

import ast
import importlib
import io
import logging
import logging.handlers
import re
import shutil
import sys
import tempfile
import threading
import types
from pathlib import Path

import gi

gi.require_versions({"Gtk": "4.0", "Adw": "1"})
from gi.repository import GLib

# Importing the real `cartridges` package needs the meson-generated `config.py`
# and compiled GSettings schemas, so stub the package and its config with only
# what `logs` uses.
_STATE_DIR = Path(tempfile.mkdtemp())
_package = types.ModuleType("cartridges")
_package.__path__ = [str(Path(__file__).resolve().parents[1] / "cartridges")]
_package.STATE_DIR = _STATE_DIR  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["cartridges"] = _package

_config = types.ModuleType("cartridges.config")
_config.APP_ID = "page.samuelm333.Cartridges.Test"  # pyright: ignore[reportAttributeAccessIssue]
_config.VERSION = "v1.2.3"  # pyright: ignore[reportAttributeAccessIssue]
_config.PROFILE = "development"  # pyright: ignore[reportAttributeAccessIssue]
_config.PREFIX = ""  # pyright: ignore[reportAttributeAccessIssue]
_config.LOCALEDIR = ""  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["cartridges.config"] = _config

logs = importlib.import_module("cartridges.logs")

_DIR = _STATE_DIR / "logs"
_FILE = _DIR / "page.samuelm333.Cartridges.Test.log"
_LINE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \[[A-Z]+\] [\w.]+: ")
_SECRET = "abcd1234efgh5678"  # noqa: S105 - fake key, only checks redaction

_logger = logging.getLogger("cartridges.test")
_failures: list[None] = []


def _run_main_loop() -> None:
    context = GLib.MainContext.default()
    while context.pending():
        context.iteration(False)


def _reset() -> None:
    logs.disable()
    _run_main_loop()
    logs.set_secret("")
    vars(logs)["_failure_reported"] = False
    vars(logs)["_failure_pending"] = False
    _failures.clear()
    shutil.rmtree(_STATE_DIR, ignore_errors=True)
    _STATE_DIR.mkdir(parents=True, exist_ok=True)


def _read() -> str:
    return _FILE.read_text(encoding="utf-8")


def _expect(actual: object, expected: object, what: str) -> None:
    if actual != expected:
        msg = f"Expected {what} to be {expected!r}, got {actual!r}"
        raise AssertionError(msg)


def _file_handlers() -> list[logging.Handler]:
    return [
        handler
        for handler in logging.getLogger().handlers
        if isinstance(handler, logging.handlers.RotatingFileHandler)
    ]


def check_enable_writes_header_and_debug() -> None:
    """Validate the header line, debug records, and the line format."""
    _reset()
    _expect(logs.enable(_DIR), True, "enable() result")
    _logger.debug("hello")
    logs.disable()

    lines = _read().splitlines()
    _expect(len(lines), 2, "number of lines")
    header = lines[0]
    _expect("cartridges.logs" in header, True, "header logger name")
    for part in ("v1.2.3", "page.samuelm333.Cartridges.Test"):
        _expect(part in header, True, f"{part!r} in header")
    _expect("development" in header, False, "build type in header")
    _expect(lines[1].endswith("[DEBUG] cartridges.test: hello"), True, "debug line")
    for line in lines:
        _expect(bool(_LINE.match(line)), True, f"format of {line!r}")


def check_disable_stops_and_keeps_files() -> None:
    """Validate that disabling stops writing without removing files."""
    _reset()
    logs.enable(_DIR)
    _logger.info("before")
    logs.disable()
    _logger.info("after")

    _expect(_FILE.exists(), True, "log file kept")
    _expect("before" in _read(), True, "record before disabling")
    _expect("after" in _read(), False, "record after disabling")


def check_no_file_when_never_enabled() -> None:
    """Validate that nothing is written while logging is off."""
    _reset()
    _logger.info("not saved")
    _expect(_DIR.exists(), False, "logs folder exists")


def check_enable_is_idempotent() -> None:
    """Validate that enabling twice does not duplicate lines or handlers."""
    _reset()
    logs.enable(_DIR)
    logs.enable(_DIR)
    _expect(len(_file_handlers()), 1, "number of file handlers")
    _logger.info("once")
    logs.disable()
    _expect(_read().count("once"), 1, "copies of the record")
    _expect(len(_file_handlers()), 0, "file handlers after disabling")


def check_key_redacted() -> None:
    """Validate that the secret never reaches the file."""
    _reset()
    logs.set_secret(_SECRET)
    logs.enable(_DIR)
    _logger.info(f"key {_SECRET} inline")  # noqa: G004
    _logger.info("key %s as argument", _SECRET)
    try:
        raise ValueError(_SECRET)
    except ValueError:
        _logger.exception("failure")
    logs.disable()

    text = _read()
    _expect(_SECRET in text, False, "secret in file")
    _expect(text.count("[redacted]"), 3, "redacted values")

    _reset()
    logs.set_secret("short")
    logs.enable(_DIR)
    _logger.info("a short value stays")
    logs.disable()
    _expect("short value" in _read(), True, "short value kept")


def check_terminal_unchanged() -> None:
    """Validate that the terminal keeps its level and output."""
    _reset()
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    stream = io.StringIO()
    terminal = logging.StreamHandler(stream)
    root.addHandler(terminal)
    try:
        logs.enable(_DIR)
        _expect(terminal.level, logging.INFO, "terminal level")
        _logger.debug("file only")
        _logger.info("both")
        logs.disable()
        _expect(root.level, logging.INFO, "root level after disabling")
    finally:
        root.removeHandler(terminal)

    _expect(stream.getvalue(), "both\n", "terminal output")
    _expect("file only" in _read(), True, "debug record in file")


def check_unwritable_folder() -> None:
    """Validate that an unusable folder reports once and raises nothing."""
    _reset()
    logs.set_failure_callback(lambda: _failures.append(None))
    blocker = _STATE_DIR / "blocker"
    blocker.write_text("", encoding="utf-8")

    _expect(logs.enable(blocker / "logs"), False, "first enable() result")
    _expect(logs.enable(blocker / "logs"), False, "second enable() result")
    _run_main_loop()
    _expect(len(_failures), 1, "failure reports")


def check_write_failure() -> None:
    """Validate that a failing write reports once and stops logging."""
    _reset()
    logs.set_failure_callback(lambda: _failures.append(None))
    _DIR.mkdir(parents=True)
    _FILE.mkdir()  # A directory cannot be opened as the log file.

    previous = logging.raiseExceptions
    logging.raiseExceptions = True
    try:
        _expect(logs.enable(_DIR), True, "enable() result")
        _logger.info("lost")
        _logger.info("lost again")
        _run_main_loop()
    finally:
        logging.raiseExceptions = previous

    _expect(len(_failures), 1, "failure reports")
    _expect(len(_file_handlers()), 0, "file handlers after failure")


def check_file_removed_while_running() -> None:
    """Validate that a removed log file is created again."""
    _reset()
    logs.enable(_DIR)
    _logger.info("first")
    _FILE.unlink()
    _logger.info("second")
    logs.disable()

    _expect(_FILE.exists(), True, "log file recreated")
    _expect("second" in _read(), True, "record after removal")


def check_rotation_caps_size() -> None:
    """Validate that rotation keeps four archives and caps the total size."""
    _reset()
    limit = 2048
    logs.enable(_DIR, max_bytes=limit, backup_count=4)
    for number in range(400):
        _logger.info("record %04d %s", number, "x" * 20)
    logs.disable()

    names = sorted(path.name for path in _DIR.iterdir())
    expected = sorted([_FILE.name] + [f"{_FILE.name}.{i}" for i in range(1, 5)])
    _expect(names, expected, "files in the logs folder")

    total = sum(path.stat().st_size for path in _DIR.iterdir())
    _expect(total <= 5 * limit + 200, True, f"total size {total} within limit")
    _expect("record 0399" in _read(), True, "newest record in current file")

    def first_number(path: Path) -> int:
        match = re.search(r"record (\d{4})", path.read_text(encoding="utf-8"))
        return int(match.group(1)) if match else -1

    newest = first_number(_DIR / f"{_FILE.name}.1")
    oldest = first_number(_DIR / f"{_FILE.name}.4")
    _expect(newest > oldest, True, "archive order")


def check_constants() -> None:
    """Validate the rotation limits."""
    _expect(logs.MAX_BYTES, 1_048_576, "maximum file size")
    _expect(logs.BACKUP_COUNT, 4, "number of archives")


def check_pillow_quiet() -> None:
    """Validate that Pillow debug records do not fill the logs."""
    _reset()
    logs.enable(_DIR)
    pil = logging.getLogger("PIL")
    _expect(pil.getEffectiveLevel(), logging.INFO, "Pillow level")
    pil.debug("chunk noise")
    logs.disable()
    _expect("chunk noise" in _read(), False, "Pillow debug record in file")
    _expect(pil.level, logging.NOTSET, "Pillow level after disabling")


def check_unhandled_exception_logged() -> None:
    """Validate that unhandled exceptions reach the file and the old hooks run."""
    _reset()
    ran: list[str] = []
    saved = (sys.excepthook, threading.excepthook, sys.unraisablehook)
    sys.excepthook = lambda *_: ran.append("main")
    threading.excepthook = lambda _: ran.append("thread")
    sys.unraisablehook = lambda _: ran.append("unraisable")
    try:
        logs.install_exception_hooks()
        logs.set_secret(_SECRET)
        logs.enable(_DIR)

        try:
            raise ValueError(_SECRET + " main")
        except ValueError:
            sys.excepthook(*sys.exc_info())  # pyright: ignore[reportArgumentType]

        def fail() -> None:
            msg = "thread failure"
            raise RuntimeError(msg)

        worker = threading.Thread(target=fail)
        worker.start()
        worker.join()

        class Unraisable:
            def __del__(self) -> None:
                msg = "unraisable failure"
                raise KeyError(msg)

        Unraisable()
        logs.disable()
    finally:
        sys.excepthook, threading.excepthook, sys.unraisablehook = saved

    text = _read()
    for part in (
        "Unhandled exception",
        "Traceback",
        "ValueError",
        "thread failure",
        "unraisable failure",
    ):
        _expect(part in text, True, f"{part!r} in file")
    _expect(_SECRET in text, False, "secret in file")
    _expect(ran, ["main", "thread", "unraisable"], "previous hooks run")


def check_annotations_resolve() -> None:
    """Validate that every annotation in logs.py resolves when evaluated eagerly.

    Python 3.13 evaluates annotations when a function is defined, 3.14 does not,
    so a name that exists only in type stubs breaks startup on 3.13 alone.
    Names imported inside a function are out of reach and are skipped.
    """
    tree = ast.parse(Path(logs.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        annotations = [arg.annotation for arg in args] + [node.returns]
        for annotation in annotations:
            if annotation is None or isinstance(annotation, ast.Constant):
                continue
            code = ast.unparse(annotation)
            try:
                eval(code, vars(logs))  # noqa: S307
            except NameError:
                continue
            except AttributeError as error:
                msg = f"{node.name}: annotation {code!r} does not resolve: {error}"
                raise AssertionError(msg) from error


if __name__ == "__main__":
    check_enable_writes_header_and_debug()
    check_disable_stops_and_keeps_files()
    check_no_file_when_never_enabled()
    check_enable_is_idempotent()
    check_key_redacted()
    check_terminal_unchanged()
    check_unwritable_folder()
    check_write_failure()
    check_file_removed_while_running()
    check_rotation_caps_size()
    check_constants()
    check_pillow_quiet()
    check_unhandled_exception_logged()
    check_annotations_resolve()
    _reset()
