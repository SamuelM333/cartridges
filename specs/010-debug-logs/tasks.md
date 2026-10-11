---

description: "Task list for the Debug Logs feature"
---

# Tasks: Debug Logs

**Input**: Design documents from `specs/010-debug-logs/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Included. The plan and quickstart call for `tests/test_logs.py` and an update to `tests/test_settings.py`. Tests follow the existing script style (see `tests/test_hidden_games.py`: stub the `cartridges` package, plain `check_*` functions, `if __name__ == "__main__":` runner, run with `python3 tests/test_logs.py`).

**Organization**: Tasks are grouped by user story so each story can be implemented and tested on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story the task belongs to (US1, US2, US3)

## Path Conventions

Single project: application code in `cartridges/`, tests in `tests/`, build files at the repository root and in `data/`. All build and check commands run inside the `gtk-dev` Distrobox container.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Branch, build-time configuration, and the new setting key.

- [X] T001 Create branch `feat/010-debug-logs` from `main` (`git switch -c feat/010-debug-logs main`)
- [X] T002 [P] Add a boolean meson option to `meson.options`: `option('nightly', type: 'boolean', value: false, description: 'Mark the build as a nightly build')`
- [X] T003 In `meson.build`, after the existing `profile` / `app_id` block, compute `build_type` as `'development'` when `profile == 'development'`, else `'nightly'` when `get_option('nightly')` is true, else `'release'`; add `'VERSION': meson.project_version()` and `'BUILD_TYPE': build_type` to the `conf` configuration_data dictionary (depends on T002)
- [X] T004 [P] Add `VERSION = "@VERSION@"` and `BUILD_TYPE = "@BUILD_TYPE@"` to `cartridges/config.py.in`, and `VERSION: str` and `BUILD_TYPE: str` to `cartridges/config.pyi`
- [X] T005 [P] Add the key to the main schema in `data/page.samuelm333.Cartridges.gschema.xml.in`, next to the other general preferences: `<key name="debug-logs" type="b"><default>false</default></key>` (data-model: type `b`, default `false`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The logs module skeleton and test scaffold that every story builds on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Add `STATE_DIR = Path(GLib.get_user_state_dir(), "cartridges")` to `cartridges/__init__.py`, next to `DATA_DIR` and `CACHE_DIR`
- [X] T007 Create `cartridges/logs.py` with SPDX header, module docstring, `_logger = logging.getLogger(__name__)`, constants `LOG_DIR: Path = STATE_DIR / "logs"`, `MAX_BYTES: int = 1_048_576`, `BACKUP_COUNT: int = 4`, and `def log_file(directory: Path = LOG_DIR) -> Path` returning `directory / f"{APP_ID}.log"`; import `STATE_DIR` from `cartridges` and `APP_ID` from `cartridges.config`. Register `'logs.py'` in the `python.install_sources(files(...))` list in `cartridges/meson.build` (keep it alphabetical)
- [X] T008 [P] Create `tests/test_logs.py` scaffold: SPDX header and docstring; stub the `cartridges` package like `tests/test_hidden_games.py` with `STATE_DIR` set to a `tempfile.mkdtemp()` path and a stub `SETTINGS` object; register a stub `cartridges.config` module in `sys.modules` with `APP_ID = "page.samuelm333.Cartridges.Test"`, `VERSION = "0.0"`, `BUILD_TYPE = "development"`, `PROFILE = "development"`, `PREFIX = ""`, `LOCALEDIR = ""`; import `cartridges.logs` via `importlib`; add a `_reset()` helper that calls `logs.disable()` and empties the temporary folder; add an empty `if __name__ == "__main__":` runner

**Checkpoint**: `python3 tests/test_logs.py` imports the module and exits 0; `meson setup _build && ninja -C _build` succeeds.

---

## Phase 3: User Story 1 - Turn on debug logging to capture a problem (Priority: P1) MVP

**Goal**: A Preferences switch that, when on, writes timestamped `DEBUG` records (with a run header, the SGDB key redacted, and terminal output unchanged) to `<state>/cartridges/logs/<APP_ID>.log`, live and from startup.

**Independent Test**: Turn the switch on, run Import Now, and confirm `<APP_ID>.log` exists in the logs folder with a header line and `DEBUG` lines from `cartridges.*` loggers; relaunch and confirm a second header followed by startup import lines (quickstart scenarios 1 to 5, 7 to 9).

### Tests for User Story 1

> Write these first and confirm they fail before implementing T014 onward.

- [X] T009 [P] [US1] In `tests/test_logs.py`, add `check_enable_writes_header_and_debug()`: `enable(tmp_dir)` returns `True`; a `logging.getLogger("cartridges.test").debug("hello")` record appears in `log_file(tmp_dir)`; the first line comes from `cartridges.logs` and contains `VERSION`, `BUILD_TYPE` and `APP_ID`; each line matches `^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \[[A-Z]+\] [\w.]+: ` (FR-004, FR-007, FR-008)
- [X] T010 [P] [US1] In `tests/test_logs.py`, add `check_disable_stops_and_keeps_files()` (after `disable()`, new records are not written and the file still exists, FR-012), `check_no_file_when_never_enabled()` (folder stays empty after logging with logging off, SC-007), and `check_enable_is_idempotent()` (calling `enable()` twice then logging once writes exactly one line for that record and the root logger has exactly one handler of the logs handler class)
- [X] T011 [P] [US1] In `tests/test_logs.py`, add `check_key_redacted()`: set the cached key with `logs.set_secret("abcd1234efgh5678")`, log it in a message, as a `%s` argument, and inside an exception traceback via `_logger.exception`; assert the key is absent from the file and `[redacted]` is present; assert a secret shorter than 8 characters is ignored (FR-013, SC-005)
- [X] T012 [P] [US1] In `tests/test_logs.py`, add `check_terminal_unchanged()`: install a `logging.StreamHandler` on the root logger before `enable()`; after `enable()` it still has level `INFO` and a `DEBUG` record is not passed to it; after `disable()` the root logger level is back to `INFO` (FR-017)
- [X] T013 [P] [US1] In `tests/test_logs.py`, add `check_unwritable_folder()`: point `enable()` at a path under a file (so `mkdir` raises `OSError`), assert it returns `False`, raises nothing, and the registered failure callback ran exactly once even after a second failing `enable()`; and `check_file_removed_while_running()`: after a first record, delete the log file, log again, and assert the file exists with the second record (FR-014, edge case)
- [X] T014 [P] [US1] In `tests/test_settings.py`, add `"debug-logs": "b"` to the `expected_keys` dictionary

### Implementation for User Story 1

- [X] T015 [US1] In `cartridges/logs.py`, add `class _LogFileHandler(logging.handlers.RotatingFileHandler)` constructed with `encoding="utf-8"`, `delay=True` and `maxBytes`/`backupCount` from parameters, with: `format()` that calls `super().format(record)` and replaces the module-level cached secret with `[redacted]` when the secret is at least 8 characters; `emit()` that, if `self.stream` is open and `Path(self.baseFilename)` no longer exists, closes the stream and sets it to `None` before calling `super().emit(record)`; and `handleError()` that does not print a traceback but calls `_report_failure()` and schedules `disable()` via `GLib.idle_add`. Use formatter `logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")` (contracts/log-file.md)
- [X] T016 [US1] In `cartridges/logs.py`, implement `enable(directory: Path = LOG_DIR, max_bytes: int = MAX_BYTES, backup_count: int = BACKUP_COUNT) -> bool` and `disable() -> None`, keeping the active handler in a module-level variable. `enable`: return `True` if already enabled; `directory.mkdir(parents=True, exist_ok=True)` inside `try`, on `OSError` call `_report_failure()` and return `False`; set every existing root handler that has level `NOTSET` to `INFO`; add the handler at level `DEBUG`; set root level `DEBUG`; write the header with `_logger.info(...)`: `Cartridges {VERSION} ({BUILD_TYPE}) {APP_ID}, flatpak={yes|no}, Python {x.y.z}, GTK {major.minor.micro}, Adwaita {major.minor.micro}, {sys.platform}` using `Path("/.flatpak-info").exists()`, `Gtk.get_major_version()` etc. and `Adw.get_major_version()` etc. `disable`: remove and close the handler and set root level back to `INFO`. Both idempotent (FR-004, FR-005, FR-008, FR-017)
- [X] T017 [US1] In `cartridges/logs.py`, add `set_failure_callback(callback: Callable[[], None]) -> None`, `set_secret(secret: str) -> None`, and `_report_failure()`, which runs only once per process (module-level flag) and calls the callback through `GLib.idle_add` so it is safe from worker threads; if no callback is registered yet, remember the failure and call the callback as soon as one is registered (FR-014)
- [X] T018 [US1] In `cartridges/logs.py`, add `setup() -> None`: import `SETTINGS` from `cartridges`; call `set_secret(SETTINGS.get_string("sgdb-key").strip())`; call `enable()` if `SETTINGS.get_boolean("debug-logs")`; connect `SETTINGS` `changed::debug-logs` to enable or disable from the new value and `changed::sgdb-key` to `set_secret` (FR-003, FR-005, FR-006)
- [X] T019 [US1] In `cartridges/__main__.py`, import `logs` from the package and call `logs.setup()` right after `logging.basicConfig(...)` and before `Application(...)` is created (FR-006)
- [X] T020 [US1] In `cartridges/application.py` `do_startup`, call `logs.set_failure_callback(...)` with a method that shows the toast `_("Could not save debug logs")` via `Window.send_toast` on the active window; if there is no active window yet, store a pending flag and send the toast at the end of `do_activate` (contracts/preferences-ui.md, FR-014)
- [X] T021 [P] [US1] In `cartridges/ui/preferences.blp`, add `Adw.PreferencesGroup troubleshooting_group` with `title: _("Troubleshooting");` on the General page between `images_group` and `danger_zone_group`, containing `Adw.SwitchRow debug_logs_switch { title: _("Debug Logs"); subtitle: _("Save detailed diagnostic messages to disk"); }` (FR-001)
- [X] T022 [US1] In `cartridges/ui/preferences.py`, add `debug_logs_switch: Adw.SwitchRow = Gtk.Template.Child()` under a `# Troubleshooting` comment and add `"debug-logs"` to the `switches` set in `_bind_switches()` (depends on T021)
- [X] T023 [US1] Add the test functions from T009 to T013 to the runner block of `tests/test_logs.py` and run `python3 tests/test_logs.py` and `python3 tests/test_settings.py` (after `meson setup _build && ninja -C _build`); both must exit 0

**Checkpoint**: Quickstart scenarios 1 to 5 and 7 to 9 pass. US1 is a shippable MVP.

---

## Phase 4: User Story 2 - Find the log files to share them (Priority: P2)

**Goal**: A Preferences row that opens the logs folder in the file manager, creating it if needed.

**Independent Test**: Delete the logs folder, activate "Open Logs Folder", and confirm the file manager opens on the (new, empty) folder; repeat with logs present; repeat in the Devel Flatpak (quickstart scenario 6).

### Implementation for User Story 2

- [X] T024 [P] [US2] In `cartridges/ui/preferences.blp`, add to `troubleshooting_group` after `debug_logs_switch`: `Adw.ActionRow logs_folder_row { title: _("Open Logs Folder"); activatable: true; activated => $_on_logs_folder_activated(); [suffix] Gtk.Image { icon-name: "folder-open-symbolic"; } }` (contracts/preferences-ui.md)
- [X] T025 [US2] In `cartridges/ui/preferences.py`, add `logs_folder_row: Adw.ActionRow = Gtk.Template.Child()`; in `__init__`, set its subtitle to `str(logs.LOG_DIR)` with the home folder shown as `~` (same `re.sub(f"^{Path.home()!s}", "~", ...)` approach as `_update_subtitles`); add `@Gtk.Template.Callback() def _on_logs_folder_activated(self, *_args: Any) -> None` that runs `logs.LOG_DIR.mkdir(parents=True, exist_ok=True)` (on `OSError` toast `_("Could not open logs folder")` and return), then `Gtk.FileLauncher(file=Gio.File.new_for_path(str(logs.LOG_DIR))).launch(parent_window, None, callback)` where the callback calls `launch_finish` in `try` and on `GLib.Error` toasts `_("Could not open logs folder")` via `_send_toast` (FR-011, depends on T024)

**Checkpoint**: Quickstart scenario 6 passes; US1 still passes.

---

## Phase 5: User Story 3 - Logs never fill the disk (Priority: P2)

**Goal**: The log folder stays at or under about 5 MiB per app ID however long logging stays on, and the newest messages are always kept.

**Independent Test**: Run `check_rotation_caps_size()` with a small limit; manually, keep logging on through heavy use and confirm `du -sh` on the logs folder never exceeds about 5 MiB.

Note: rotation is provided by the handler from T015 and T016; this phase locks in the limits, protects the budget from library noise, and tests it.

### Tests for User Story 3

- [X] T026 [P] [US3] In `tests/test_logs.py`, add `check_rotation_caps_size()`: `enable(tmp_dir, max_bytes=2048, backup_count=4)`, log 400 numbered records of about 60 bytes, then assert the folder holds exactly `<APP_ID>.log` and `<APP_ID>.log.1` to `.log.4`, total size is at most `5 * 2048 + 200` bytes, the last record number is in `<APP_ID>.log`, and `.log.1` holds newer records than `.log.4`; add it to the runner (FR-010, SC-003)
- [X] T027 [P] [US3] In `tests/test_logs.py`, add `check_constants()` asserting `logs.MAX_BYTES == 1_048_576` and `logs.BACKUP_COUNT == 4`, and `check_pillow_quiet()` asserting that after `enable()` `logging.getLogger("PIL")` has effective level `INFO` and a `PIL` `DEBUG` record is not written; add both to the runner

### Implementation for User Story 3

- [X] T028 [US3] In `cartridges/logs.py` `enable()`, set `logging.getLogger("PIL").setLevel(logging.INFO)` before adding the handler, and in `disable()` restore it to `logging.NOTSET` (research R4); run `python3 tests/test_logs.py` and confirm exit 0

**Checkpoint**: All three stories pass their independent tests.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Nightly build type, docs, and the constitution quality gate.

- [X] T029 [P] In `.github/workflows/nightly.yml`, add a step before "Build Nightly Flatpak Bundle" with the same `if:` condition that appends `-Dnightly=true` to the `config-opts` of the module named `cartridges` in `flatpak/page.samuelm333.Cartridges.json`: `jq '(.modules[] | select(type == "object" and .name == "cartridges") | ."config-opts") += ["-Dnightly=true"]' flatpak/page.samuelm333.Cartridges.json > manifest.tmp && mv manifest.tmp flatpak/page.samuelm333.Cartridges.json`. If `jq` is not present in the `gnome-50` container image, use an equivalent `python3 -c` one-liner with the `json` module. Do not change `flatpak/page.samuelm333.Cartridges.json` in git (research R6)
- [X] T030 [P] Add a short "Debug logs" section to `README.md` (or `CONTRIBUTING.md` if README has no troubleshooting content) stating how to turn logs on (Preferences > General > Troubleshooting) and the folder locations from `specs/010-debug-logs/contracts/log-file.md`
- [X] T031 Confirm `po/POTFILES.in` already lists every file with new translatable strings (`cartridges/application.py`, `cartridges/ui/preferences.blp`, `cartridges/ui/preferences.py`); add any that are missing, keeping the list sorted
- [X] T032 Run `pre-commit run --all-files`, `ruff check`, and `pyright` (strict) and fix every reported problem in the changed files
- [X] T033 Run `meson setup --wipe _build && ninja -C _build test`, then `python3 tests/test_logs.py` and `python3 tests/test_settings.py`; all must pass
- [ ] T034 Walk through every manual scenario in `specs/010-debug-logs/quickstart.md` with a development build, plus a build configured with `-Dnightly=true` to confirm the header reads `nightly`
- [X] T035 Run `python3 .specify/scripts/bash/check-emojis.py` and confirm no emoji were introduced in code, strings or docs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. T003 depends on T002.
- **Foundational (Phase 2)**: Depends on Phase 1 (T007 needs T004 for `APP_ID`, T006 for `STATE_DIR`). Blocks all stories.
- **US1 (Phase 3)**: Depends on Phase 2.
- **US2 (Phase 4)**: Depends on Phase 2 and on T021 (the `troubleshooting_group` it adds a row to). Does not need logging to work; the folder can be opened with logging off.
- **US3 (Phase 5)**: Depends on T015 and T016 from US1 (the handler it constrains).
- **Polish (Phase 6)**: Depends on the stories being shipped. T029 and T030 can start any time after Phase 1.

### Within User Story 1

- T009 to T014 (tests) before T015 to T023.
- T015 then T016 then T017 then T018 (same file, `cartridges/logs.py`).
- T019 and T020 after T018.
- T021 can run alongside T015 to T018; T022 after T021.

### Parallel Opportunities

- Phase 1: T002, T004, T005 in parallel.
- Phase 2: T008 in parallel with T006 and T007.
- US1: T009 to T014 in parallel (T009 to T013 all edit `tests/test_logs.py`, so parallelize only if merging function additions; T014 is a different file); T021 in parallel with the `logs.py` work.
- US2 T024 and US3 T026/T027 can start as soon as their dependencies above are met, in parallel with each other.
- Polish: T029 and T030 in parallel.

---

## Parallel Example: User Story 1

```text
Task: "T014 Add debug-logs to expected_keys in tests/test_settings.py"
Task: "T021 Add troubleshooting_group with debug_logs_switch in cartridges/ui/preferences.blp"
Task: "T015 Add _LogFileHandler in cartridges/logs.py"
```

## Parallel Example: User Stories 2 and 3 (after US1 T021 and T016)

```text
Task: "T024 Add logs_folder_row in cartridges/ui/preferences.blp"
Task: "T026 Add check_rotation_caps_size in tests/test_logs.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup.
2. Phase 2: Foundational.
3. Phase 3: US1.
4. Stop and validate with quickstart scenarios 1 to 5 and 7 to 9.

The default 1 MiB x 5 rotation is already active after US1 because the handler is a rotating handler; US3 adds the tests and the Pillow noise clamp that keep the cap meaningful.

### Incremental Delivery

1. Setup + Foundational.
2. US1: switch, file logging, redaction, failure toast (MVP).
3. US2: open-folder row.
4. US3: rotation verification and noise control.
5. Polish: nightly build type in CI, docs, quality gate.

---

## Notes

- [P] tasks touch different files and have no dependency on incomplete tasks.
- Commit after each task or logical group, on `feat/010-debug-logs`.
- Never print or log the SteamGridDB key in tests' failure messages; compare with `in` and report only a boolean.

---

## Phase 7: Convergence

**Purpose**: Close the gaps found by `/speckit-converge`. Source of the first group: your directive that the log header show the release tag (`vx.y.z` for releases, `nightly-<short commit>` for nightly builds), that CI guarantee `jq`, and that the Python fallback be removed. This phase supersedes the `-Dnightly=true` approach in T002, T003, T004, T029 and the `-Dnightly=true` check in T034.

- [X] T036 Replace the nightly flag with a tag option: in `meson.options` remove the `nightly` boolean and add `option('tag', type: 'string', value: '', description: 'Release tag shown in debug logs, for example v1.2.3 or nightly-abc1234')`; in `meson.build` remove the `build_type` block and the `'BUILD_TYPE'` entry, and set `'VERSION'` to the `tag` option when it is not empty, else to `'development'` when `profile == 'development'`, else `meson.project_version()`; remove `BUILD_TYPE` from `cartridges/config.py.in` and `cartridges/config.pyi`, keeping `VERSION` (now holding the tag) per FR-008 as amended (contradicts)
- [X] T037 Show the tag in the log header: in `cartridges/logs.py` drop the `BUILD_TYPE` import and change the header to `Cartridges {VERSION} {APP_ID}, flatpak=..., Python ..., GTK ..., Adwaita ..., {sys.platform}`; in `tests/test_logs.py` remove the `_config.BUILD_TYPE` stub, set `_config.VERSION = "v1.2.3"`, and update `check_enable_writes_header_and_debug` to assert `v1.2.3` is in the header and `development` is not per FR-008 as amended (contradicts)
- [X] T038 Create `.github/scripts/set_build_tag.sh` (executable, `set -euo pipefail`, one argument: the tag): fail with a clear error if `jq` is not on `PATH` (no installer and no Python fallback, because the `ghcr.io/flathub-infra/flatpak-github-actions:gnome-50` image is Freedesktop SDK 25.08 with no package manager and already ships `jq` 1.8.2 at `/app/bin/jq`); reject any tag not matching `^[A-Za-z0-9._-]+$`; use `jq --arg tag "$1"` to append `-Dtag=$tag` to the `config-opts` of the module named `cartridges` in `flatpak/page.samuelm333.Cartridges.json`, write through a temporary file then move it into place, and confirm the result with `jq -e` per FR-008 as amended (missing)
- [X] T039 In `.github/workflows/nightly.yml` replace the "Mark Build as Nightly" step (including its Python fallback) with a "Set Build Tag" step that keeps the same `if:` condition and runs `.github/scripts/set_build_tag.sh "nightly-${{ steps.commit.outputs.short }}"`, so the tag matches the `tag_name` used by "Publish Nightly Release" per FR-008 as amended (partial)
- [X] T040 In `.github/workflows/publish-release.yml` add a "Set Build Tag" step after "Checkout" and before "Build Flatpak Bundle" that runs `.github/scripts/set_build_tag.sh "${GITHUB_REF#refs/tags/}"`, so a release built from tag `v1.2.3` logs `v1.2.3`; leave "Get Tag Name" unchanged per FR-008 as amended (missing)
- [X] T041 Log the import: in `cartridges/importer.py` add `_logger = logging.getLogger(__name__)` and write DEBUG or INFO records for import start, each source started and finished with its game count, and import finished with the number of new games and the elapsed time; log game titles and IDs only, never settings values such as keys per FR-004, SC-002, US1/AC2 (partial)
- [X] T042 Log source scanning at DEBUG level in `cartridges/sources/steam.py`, `lutris.py`, `heroic.py`, `itch.py`, `legendary.py`, `flatpak.py`, `desktop.py` and `imported.py`: the location scanned, how many games were found, and why entries were skipped when it is cheap to say; keep sources free of GUI imports per Constitution II (partial: FR-004, US1/AC2)
- [X] T043 Add a test in `tests/test_importer.py` (or `tests/test_logs.py` if the importer test cannot run an import with a stub) that runs an import with logging enabled and asserts at least one record from a `cartridges.importer` logger reaches the log file per SC-002 (partial)
- [X] T044 Update the documents to the tag-based design in `specs/010-debug-logs/`: `spec.md` FR-008 (the first line names the app version as the release tag: `vx.y.z` for releases, `nightly-<short commit>` for nightly builds, `development` for development builds), FR-015, FR-016 and SC-006 where they mention build type; `plan.md` summary, source layout and the Complexity Tracking row (remove the `nightly` option, add `tag` and `set_build_tag.sh`); `research.md` R6 (rewrite, including the jq check and why a Python fallback was dropped); `data-model.md` build information table; `contracts/log-file.md` header example and guarantee 1, and replace the `cartridges.importer: Scanning source steam` example with a message T041 and T042 really emit; `quickstart.md` "Build types" section (use `-Dtag=`) per FR-008 as amended (partial)
- [X] T045 Validate the tag flow: `meson setup _build_tag -Dprofile=release -Dtag=nightly-abc1234` gives `VERSION = "nightly-abc1234"` in `_build_tag/cartridges/config.py`; a development build with no tag gives `development`; run `.github/scripts/set_build_tag.sh` against a copy of the manifest with a valid tag (the module's `config-opts` gain `-Dtag=...`), an invalid tag such as `a b;c` (rejected, manifest unchanged), and with `jq` removed from `PATH` (clear error, non-zero exit); then run `python3 tests/test_logs.py`, `python3 tests/test_importer.py` and `uv run pre-commit run --all-files`. This replaces the `-Dnightly=true` check in T034 per FR-008 as amended (partial)

## Phase 8: Convergence

**Purpose**: Close the gap found by `/speckit-converge` (directive: review whether unhandled exceptions are written to the log). Python's default `sys.excepthook`, `threading.excepthook`, and `sys.unraisablehook` print to stderr only, so an exception that escapes a GTK callback or a worker thread never reaches the root logger and therefore never reaches the debug log file. `cartridges/__main__.py` and `cartridges/logs.py` install no such hook. Only exceptions caught by an explicit `_logger.exception` or by asyncio's own `asyncio` logger are written.

- [X] T046 CRITICAL Install logging hooks for unhandled exceptions in `cartridges/logs.py` (called from `setup()`, or a small `install_exception_hooks()` called from `cartridges/__main__.py` right after `logs.setup()`): replace `sys.excepthook`, `threading.excepthook`, and `sys.unraisablehook` with functions that log the exception at CRITICAL/ERROR on a module-level logger with `exc_info`, then delegate to the previous hook so terminal output is unchanged; logging must happen whether Debug Logs is on or off at that moment so a later switch-on is not required (the file handler only receives records while enabled) per Constitution VII and FR-004 (partial)
- [X] T047 Add `check_unhandled_exception_logged()` in `tests/test_logs.py`: with logging enabled to a temp directory, call `sys.excepthook` and `threading.excepthook` (via a thread that raises) with a known exception, and assert the log file contains the message, `Traceback`, and the exception text, that the SteamGridDB key is still redacted (FR-013), and that the previous hook still ran (FR-017) per FR-004, Constitution VII (missing)
- [X] T048 Update `specs/010-debug-logs/contracts/log-file.md` and `quickstart.md` (append-only wording changes) to state that unhandled exceptions from callbacks, threads, and unraisable errors are recorded with their traceback, and run the quickstart check with Debug Logs on and a deliberately raised error per FR-004 (partial)

## Phase 9: Convergence

**Purpose**: Close the gap found by `/speckit-converge` (report: the app does not start). `install_exception_hooks()` in `cartridges/logs.py` annotates `unraisable_hook(args: sys.UnraisableHookArgs)`. `sys.UnraisableHookArgs` exists only in type stubs, not at runtime, and Python 3.13 (the Flatpak runtime) evaluates annotations when the function is defined, so `logs.setup()` raises `AttributeError` and aborts startup. The local venv runs Python 3.14, which defers annotation evaluation, so `tests/test_logs.py` passed and hid the failure.

- [X] T049 CRITICAL Fix the startup crash in `cartridges/logs.py` `install_exception_hooks()`: stop referencing `sys.UnraisableHookArgs` at runtime (for example, annotate `args` with a name imported under `if TYPE_CHECKING:` and a string annotation, or `from __future__ import annotations`), and confirm `threading.ExceptHookArgs` and every other annotation in the function resolve on Python 3.13 per Constitution VII and FR-014 (contradicts)
- [X] T050 Add a regression check to `tests/test_logs.py` that fails on Python 3.13: call `logs.install_exception_hooks()` and `logs.setup`'s import path under an interpreter that evaluates annotations eagerly (for example, run the module with `python3.13` when available, or assert via `typing.get_type_hints`/`inspect.get_annotations(eval_str=True)` that the nested hook functions' annotations resolve), so a runtime-missing name cannot pass on 3.14 only per FR-004 (missing)
- [X] T051 Run the test suite and a startup smoke test on the Flatpak runtime Python (3.13): `python3.13 tests/test_logs.py` or a Devel Flatpak build, and launch the app once with Debug Logs on and off per SC-004 (missing)

## Phase 10: Convergence

**Purpose**: Close the gap found by `/speckit-converge` (directive: check the pyright error in the PR). The `Lint & Validation` check on PR #28 fails in the `pyright` pre-commit gate with 2 errors, both at `tests/test_logs.py:332`: `Path(logs.__file__)` passes `str | None` where `StrPath` is expected, because a module's `__file__` is optional in the stubs. The local venv cannot resolve `gi`, so these errors were not visible before pushing, and the commits skipped the gate with `SKIP=pyright`.

- [X] T052 CRITICAL Fix the 2 pyright `reportArgumentType` errors in `tests/test_logs.py` `check_annotations_resolve()` (line 332): read the source without `logs.__file__`, for example `inspect.getsource(logs)` or `Path(__file__).resolve().parents[1] / "cartridges" / "logs.py"`, so the argument is a `str` or `Path` per Constitution I (strict Pyright must pass before merge) (contradicts)
- [ ] T053 Confirm the `Lint & Validation` check on PR #28 passes (`gh pr checks 28`) after the fix, and do not use `SKIP=pyright` again for this branch per Constitution I (missing)
