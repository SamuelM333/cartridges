# Implementation Plan: Debug Logs

**Branch**: `feat/010-debug-logs` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-debug-logs/spec.md`

## Summary

Add a "Debug Logs" switch to Preferences > General that, when on, attaches a size-rotating file handler (1 MiB x 5 files) to Python's root logger and writes `DEBUG`-level, timestamped records to `$XDG_STATE_HOME/cartridges/logs/<APP_ID>.log`. Logging starts before the `Application` is created so startup is captured, toggles live through a GSettings change signal, redacts the stored SteamGridDB key, never changes terminal output, and reports write failures with a single toast. A second row opens the logs folder in the file manager. The release tag (`vx.y.z` for releases, `nightly-<short commit>` for nightly builds, `development` for development builds) is baked into `config.py` and written in a header line on each run.

## Technical Context

**Language/Version**: Python 3.13+ (`requires-python >= 3.13`)

**Primary Dependencies**: PyGObject with GTK 4, Libadwaita 1, GLib/Gio; Python stdlib `logging.handlers`. No new dependencies.

**Storage**: GSettings key `debug-logs` (bool); plain-text UTF-8 log files in the XDG state folder.

**Testing**: Script-style tests in `tests/` run with `python3 tests/test_*.py` (package stubbed as in `tests/test_hidden_games.py`); schema check in `tests/test_settings.py`; `ninja -C _build test` for data validation.

**Target Platform**: Linux desktop, Flatpak first (`page.samuelm333.Cartridges` and `.Devel`); host builds via meson.

**Project Type**: Desktop application (GNOME).

**Performance Goals**: Logging off: zero file I/O. Logging on: no perceptible UI delay; one `stat` and one buffered write per record.

**Constraints**: At most about 5 MiB of logs per app ID; no new Flatpak permissions; terminal output unchanged; credentials never written.

**Scale/Scope**: 1 new module (`cartridges/logs.py`), 1 new test file, edits to about 9 existing files, 1 new GSettings key, 1 new meson option.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | How the design complies |
|-----------|--------|-------------------------|
| I. Strict typing and QA | Pass | `cartridges/logs.py` fully annotated, no `Any`; `config.pyi` keeps a typed `VERSION`, which now holds the tag; pre-commit, Ruff and Pyright strict run before completion. |
| II. Modular game sources | Pass (N/A) | No source changes. Sources keep logging through their own `logging.getLogger(__name__)`. |
| III. Blueprint-driven UI | Pass | New rows declared in `cartridges/ui/preferences.blp`; controller only binds and handles activation. |
| IV. Libadwaita, HIG, sandbox | Pass | Standard `Adw.PreferencesGroup`, `Adw.SwitchRow`, `Adw.ActionRow`; toasts for non-critical failures; folder opened via `Gtk.FileLauncher` (OpenURI portal under Flatpak); writes only to the app's own state folder, no new `finish-args`. |
| V. Resource sandboxing (XDG) | Pass | Logs live in the XDG state folder beside the existing data and cache folders; no blocking work beyond buffered appends. |
| VI. Emoji-free | Pass | No emoji in code, strings, or docs. |
| Dev environment | Pass | All checks run in `gtk-dev`; see [quickstart.md](quickstart.md). |
| Branching | Pass | `feat/010-debug-logs` from `main`. |

**Post-design re-check (after Phase 1)**: Pass. The CI changes (the nightly and release workflows calling one script, `set_build_tag.sh`, which passes the tag to the build) touch no principle; the release manifest in git is unchanged.

## Project Structure

### Documentation (this feature)

```text
specs/010-debug-logs/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── log-file.md
│   └── preferences-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks (not created here)
```

### Source Code (repository root)

```text
meson.options                                   # + 'tag' string option
meson.build                                     # + VERSION from the tag (or 'development', or the project version)
cartridges/
├── config.py.in                                # + VERSION
├── config.pyi                                  # + VERSION: str
├── __init__.py                                 # + STATE_DIR (cartridges subfolder of user state dir)
├── __main__.py                                 # call logs.setup() after basicConfig
├── logs.py                                     # NEW: handler, redaction, toggle, header, failure callback
├── meson.build                                 # install logs.py
├── application.py                              # register failure callback -> toast once
└── ui/
    ├── preferences.blp                         # + Troubleshooting group
    └── preferences.py                          # + bind debug-logs, open folder row
data/page.samuelm333.Cartridges.gschema.xml.in  # + debug-logs key
po/POTFILES.in                                  # (no change if strings stay in listed files)
.github/
├── scripts/set_build_tag.sh                    # NEW: add -Dtag=<tag> to the manifest with jq
├── workflows/nightly.yml                       # call it with nightly-<short commit>
└── workflows/publish-release.yml               # call it with the pushed tag
tests/
├── test_logs.py                                # NEW
└── test_settings.py                            # + debug-logs in expected keys
```

**Structure Decision**: Single-project desktop app. Logging lives in one new top-level module `cartridges/logs.py`, next to the other app-wide services (`hidden_games.py`, `saved_library.py`), so it has no UI dependency and is testable with the existing package-stub pattern. The UI controller and `Application` depend on it, never the reverse; the failure toast is delivered through a callback the `Application` registers.

### `cartridges/logs.py` shape (interface only)

```text
LOG_DIR: Path                         # STATE_DIR / "logs"
MAX_BYTES = 1_048_576
BACKUP_COUNT = 4

setup() -> None                       # read SETTINGS, apply, connect changed::debug-logs and changed::sgdb-key
enable(directory: Path = LOG_DIR, max_bytes: int = MAX_BYTES, backup_count: int = BACKUP_COUNT) -> bool
disable() -> None
set_failure_callback(callback: Callable[[], None]) -> None
set_secret(secret: str) -> None       # value redacted from file output (SteamGridDB key)
log_file() -> Path                    # LOG_DIR / f"{APP_ID}.log"
```

`enable`/`disable` are idempotent and take the folder and limits as parameters so tests can use a temporary folder and a tiny size limit.

## Complexity Tracking

No constitution violations to justify.

| Decision | Why Needed | Simpler Alternative Rejected Because |
|----------|------------|--------------------------------------|
| New `tag` meson option and `set_build_tag.sh`, called by the nightly and release workflows | FR-008 requires logs to name the release tag; nightly and release share one manifest and app ID, so nothing at runtime tells them apart | `vcs_tag()` commit hash: `.git` may be absent in the Flatpak `dir` source, so it would read "unknown"; editing the manifest in git would make every release report the nightly tag |
