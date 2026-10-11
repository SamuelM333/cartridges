# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Test that no exception handler in the application discards an error silently.

A handler must log the error, re-raise it, or carry a `# silent-ok: <reason>`
comment on its line or the line above, for errors that are normal control flow
or an absent optional value (Principle VII of the constitution).
"""

import ast
from pathlib import Path

_APP = Path(__file__).resolve().parents[1] / "cartridges"

# Logging cannot report its own failures.
_EXEMPT = {"logs.py"}

_LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical"}
_MARKER = "# silent-ok:"


def _logs_or_raises(nodes: list[ast.stmt]) -> bool:
    for node in nodes:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Raise):
                return True
            if (
                isinstance(sub, ast.Call)
                and isinstance(sub.func, ast.Attribute)
                and sub.func.attr in _LOG_METHODS
            ):
                return True
    return False


def _is_suppress(node: ast.expr) -> bool:
    return isinstance(node, ast.Call) and ast.unparse(node.func) in {
        "suppress",
        "contextlib.suppress",
    }


def _marked(lines: list[str], lineno: int) -> bool:
    """Whether the line `lineno` (1-based) or the one above has the marker."""
    return any(_MARKER in lines[i] for i in (lineno - 1, lineno - 2) if i >= 0)


def silent_handlers(source: str) -> list[tuple[int, str]]:
    """Find the handlers in `source` that neither log, re-raise, nor are marked."""
    lines = source.splitlines()
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ExceptHandler):
            if not _logs_or_raises(node.body) and not _marked(lines, node.lineno):
                found.append((
                    node.lineno,
                    f"except {ast.unparse(node.type or ast.Name('bare'))}",
                ))
        elif (
            isinstance(node, ast.With)
            and any(_is_suppress(item.context_expr) for item in node.items)
            and not _marked(lines, node.lineno)
        ):
            found.append((node.lineno, "with suppress(...)"))
    return found


def _expect(actual: object, expected: object, what: str) -> None:
    if actual != expected:
        msg = f"Expected {what} to be {expected!r}, got {actual!r}"
        raise AssertionError(msg)


def check_scanner_can_fail() -> None:
    """Validate the scanner on sample code, so a pass means something."""
    silent = "try:\n    work()\nexcept OSError:\n    pass\n"
    _expect(len(silent_handlers(silent)), 1, "silent handlers in a bare pass")

    suppressed = "with suppress(OSError):\n    work()\n"
    _expect(len(silent_handlers(suppressed)), 1, "silent handlers in suppress")

    logged = "try:\n    work()\nexcept OSError as e:\n    _logger.debug('x %s', e)\n"
    _expect(silent_handlers(logged), [], "silent handlers when logged")

    raised = "try:\n    work()\nexcept OSError as e:\n    raise ValueError from e\n"
    _expect(silent_handlers(raised), [], "silent handlers when re-raised")

    same_line = (
        "try:\n    work()\nexcept OSError:  # silent-ok: not an error\n    pass\n"
    )
    _expect(silent_handlers(same_line), [], "silent handlers with a marker")

    line_above = (
        "try:\n    work()\n# silent-ok: not an error\nexcept OSError:\n    pass\n"
    )
    _expect(silent_handlers(line_above), [], "silent handlers with a marker above")


def check_no_silent_handlers() -> None:
    """Validate that every handler in the application logs or is marked."""
    problems = [
        f"{path.relative_to(_APP.parent)}:{lineno}: {what}"
        for path in sorted(_APP.rglob("*.py"))
        if path.name not in _EXEMPT
        for lineno, what in silent_handlers(path.read_text(encoding="utf-8"))
    ]
    if problems:
        msg = "Handlers that discard errors silently:\n  " + "\n  ".join(problems)
        raise AssertionError(msg)


if __name__ == "__main__":
    check_scanner_can_fail()
    check_no_silent_handlers()
