# Research: Debug Logs

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## R1. Log folder location

- **Decision**: `Path(GLib.get_user_state_dir(), "cartridges", "logs")`.
- **Rationale**: The XDG Base Directory spec names `$XDG_STATE_HOME` (default `~/.local/state`) as the place for "actions history (logs, history, recently used files, ...)". `GLib.get_user_state_dir()` (GLib 2.72+) resolves it and honours the env var. Inside Flatpak, `XDG_STATE_HOME` is set to `~/.var/app/<app id>/.local/state`, so the folder is private to the app ID and writable without any new `finish-args`. The `cartridges` subfolder mirrors the existing `DATA_DIR` and `CACHE_DIR` in `cartridges/__init__.py`.
- **Alternatives considered**:
  - `GLib.get_user_data_dir()` (what the request mentioned): works, but data is for user content that must survive; logs are disposable state. Backups and sync tools treat the two differently.
  - `GLib.get_user_cache_dir()`: cache may be cleared by the system at any time, which would delete the very logs a user is about to attach.
  - systemd journal: not reachable or discoverable for typical users, and not accessible from the Flatpak sandbox in a portable way.

## R2. Keeping builds apart (FR-016)

- **Decision**: Name the log file after the app ID: `<logs>/<APP_ID>.log`, e.g. `page.samuelm333.Cartridges.log` and `page.samuelm333.Cartridges.Devel.log`.
- **Rationale**: Under Flatpak each app ID already has its own state folder. Non-Flatpak builds (meson devenv, distro packages) share `~/.local/state/cartridges`, the same way they already share `DATA_DIR`; the app-ID filename keeps release and development logs separate there too. The setting itself is already per build because each profile installs its own GSettings schema ID.
- **Note on nightly**: Nightly is built from the release manifest and has the release app ID, so nightly and release cannot be installed side by side as Flatpaks. They share a folder only when one replaces the other, which is correct: the header line (R6) still tells them apart.

## R3. Writing and rotating files

- **Decision**: A small subclass of `logging.handlers.RotatingFileHandler` attached to the root logger, with `maxBytes=1 MiB`, `backupCount=4`, `encoding="utf-8"`, `delay=True`.
- **Rationale**: Standard library, thread-safe (the app logs from `asyncio.to_thread` workers), and already does size-based rotation with numbered archives (`.log.1` newest to `.log.4` oldest). With 1 MiB and 4 archives the total is capped at 5 MiB (FR-010, SC-003); a single record can overshoot by at most its own size, which is negligible for log lines.
- **Alternatives considered**:
  - `TimedRotatingFileHandler`: rotates on time, not size; the spec asks for size.
  - GLib structured logging (`GLib.log_set_writer_func`): Python modules log through `logging`, not GLib, so it would capture the wrong stream and add complexity.
  - A third-party library such as `loguru`: a new dependency for something the stdlib does; would also need a Flatpak module.

## R4. Detail level without changing the terminal (FR-004, FR-017)

- **Decision**: When enabled, set the root logger to `DEBUG` and the file handler to `DEBUG`. Set the existing stderr handler (from `logging.basicConfig` in `cartridges/__main__.py`) to an explicit `INFO` level so it keeps its current output. When disabled, restore the root logger to `INFO`.
- **Rationale**: Root level gates every handler, so lowering it is required to get debug records at all; pinning the stderr handler's own level keeps the terminal output unchanged.
- **Noise control**: Pillow emits large volumes of `DEBUG` records while decoding images (chunk-by-chunk PNG parsing). The `PIL` logger is set to `INFO` so it cannot rotate useful app messages out of the 5 MiB budget.

## R5. Live toggle and early start (FR-005, FR-006)

- **Decision**: New module `cartridges/logs.py` with `setup()` called in `cartridges/__main__.py` right after `logging.basicConfig` and before `Application(...)`. `setup()` applies the current value of the `debug-logs` key and connects to `SETTINGS` `changed::debug-logs` to attach or detach the handler at runtime.
- **Rationale**: `SETTINGS` is created on import of the `cartridges` package, which happens before `__main__` runs, so the setting is readable before startup and the startup import. GSettings change notifications arrive on the main loop; the handler attach/detach is guarded by a module-level reference so repeated toggles never add a second handler (edge case: duplicate lines).

## R6. Run header (FR-008)

- **Decision**: On every attach, log one `INFO` line from the `cartridges.logs` logger: app name, version, build type, app ID, whether running in Flatpak, Python, GTK and Libadwaita versions, and `sys.platform`.
- **Build type source**: Add `VERSION` (from `meson.project_version()`) and `BUILD_TYPE` to `cartridges/config.py.in` / `config.pyi`. `BUILD_TYPE` is `"development"` for `-Dprofile=development`, `"nightly"` when a new boolean meson option `nightly` is true, otherwise `"release"`. The nightly workflow passes `-Dnightly=true` by appending it to the cartridges module `config-opts` with `jq` before the build step, so the shared release manifest stays unchanged for real releases.
- **Flatpak detection**: `Path("/.flatpak-info").exists()`, the standard check.
- **Alternatives considered**: embedding the git commit with meson `vcs_tag()`: the Flatpak `dir` source may not carry `.git`, so it would read "unknown" in exactly the builds that matter. Can be added later; not required by the spec.

## R7. Keeping the SteamGridDB key out (FR-013)

- **Decision**: The file handler's `format()` redacts the current `sgdb-key` value from the fully formatted text (message, arguments and traceback) by replacing it with `[redacted]`. The key is cached in the logs module and refreshed on `changed::sgdb-key`; empty or very short values (fewer than 8 characters) are not used as redaction patterns to avoid mangling ordinary text.
- **Rationale**: Redacting the final string covers every path (f-strings, `%` args, exception messages, URLs) without trusting every call site. The HTTP client in `cartridges/utils/steamgriddb.py` is `urllib.request`, which does not log request headers, so there is no library-level leak to plug. Terminal output is unchanged by this (FR-017) and already does not print the key.
- **Alternatives considered**: a `logging.Filter` that rewrites `record.msg`: misses `exc_text` and arguments formatted later.

## R8. Write failures (FR-014)

- **Decision**:
  - Creating the folder: `mkdir(parents=True, exist_ok=True)` in `try`; on `OSError`, do not attach the handler and report a failure.
  - Writing: override `handleError()` so a failed write reports a failure instead of printing a traceback for every record, then stops writing for the rest of the run (handler detached) to avoid error storms.
  - Reporting: the logs module exposes a single "write failed" callback that the `Application` registers; it runs via `GLib.idle_add` (writes can fail on worker threads) and shows one toast per run: "Could not save debug logs". The switch is not flipped back.
- **File removed while running**: before each emit, if the open stream's file no longer exists at the expected path, close it so `delay=True` reopens a fresh file on the next record (same idea as `WatchedFileHandler`, without the extra device/inode bookkeeping).

## R9. Opening the folder (FR-011)

- **Decision**: `Gtk.FileLauncher(file=Gio.File.new_for_path(str(LOG_DIR))).launch(window, None, callback)`, after creating the folder if needed (US2 scenario 3). Errors are shown as a toast.
- **Rationale**: `Gtk.FileLauncher` uses the OpenURI portal when sandboxed, which opens the folder in the host file manager; the app-private state folder is a real host path, so no document-portal export is needed. Outside Flatpak it falls back to the default handler for `inode/directory`.
- **Alternative considered**: `open_containing_folder()` on the current log file: highlights the file, but fails when no log has been written yet.

## R10. Preferences UI (FR-001, FR-011)

- **Decision**: A new `Adw.PreferencesGroup` titled "Troubleshooting" on the General page, placed above "Danger Zone", containing:
  - `Adw.SwitchRow` "Debug Logs", subtitle "Save detailed diagnostic messages to disk", bound to `debug-logs` through the existing `_bind_switches()` mechanism.
  - `Adw.ActionRow` "Open Logs Folder", activatable, with the folder path (home shortened to `~`) as subtitle and a `folder-open-symbolic` suffix icon.
- **Rationale**: Uses only standard Libadwaita rows (constitution IV). The folder row stays available when logging is off so users can reach logs from an earlier session.
