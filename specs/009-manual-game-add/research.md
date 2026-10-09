# Technical Research: Manual Game Add

**Branch**: `feat/009-manual-game-add`
**Feature**: `specs/009-manual-game-add`
**Date**: 2026-10-09

## 1. What Is Already in Place

### Findings
- Add Game: `GameActions` action `add` calls `add()` in `cartridges/ui/games.py`, which opens the details page in edit mode; Apply runs `GameDetails._apply`, which calls `GameEditable.apply()`.
- `GameEditable.apply()` creates the game with `imported.new()`, appends it to the `imported` source (`sources.get(imported.ID).append(game)`), then copies `executable`, `name`, and `developer` onto it.
- `Game.save()` (`cartridges/games.py`) writes every property in `PROPERTIES` to `GAMES_DIR / f"{game_id}.json"`.
- `imported.get_games()` reads `GAMES_DIR/imported_*.json` on every start. `Source.__init__` always scans the `imported` source, even when "Import Games on Startup" is off. Damaged or unsupported files are skipped (`JSONDecodeError`, `UnicodeDecodeError`, `TypeError`).
- `importer.import_games()` skips the `imported` source, so imports never touch manual games (FR-009 already holds).
- Hidden state persists in `hidden.json` for every source, last-played time in `last-played.json`, and collections in GSettings (features 005 and 008).
- Cover files are written by `GameDetails._apply` into `COVERS_DIR` under the game ID, and `imported.get_games()` reloads them by ID.

### The gap
`game.save()` has exactly one caller: `Source._track` connects it to `notify::removed` for the `imported` source (`sources/__init__.py`). Nothing saves on add or edit. Consequences:
- A game applied in the form exists only in memory. Restarting loses it (FR-002, FR-003, FR-004 not met), unless the user later removes it, which would write a record for a game they just deleted.
- `imported.new()` computes the next number from files on disk (`get_paths()`), so while the first game is unsaved, the second also gets number 0 and the same `game_id`; saving later would overwrite one with the other (FR-008).
- `_get_collections` drops `imported_*` IDs that have no file on disk, so a manual game in a collection loses that membership after a restart (FR-007).

## 2. Where to Save: Apply, Not Shutdown

### Decision
Call `game.save()` at the end of `GameEditable.apply()` when the game belongs to the `imported` source.

### Rationale
- It satisfies FR-004 (saved when applied, so a crash or "Exit After Launching Games" cannot lose it) with one call at the single place edits are committed. Cancel never reaches `apply()`, so cancelled edits are never saved (FR-003, User Story 2 scenario 3).
- Saving after the values are copied means the file always holds the final values; the form validates before `apply()` runs (`valid` guard).
- The call site is in the UI layer, which owns toasts, so the failure notice can be raised next to it.

### Alternatives Considered
- *Save on `notify` of each editable property (`name`, `executable`, `developer`) in `Source._track`*: Rejected. It writes the file up to three times per Apply and could save half-edited states; it hides the save point from the code that has the context to report errors.
- *Save at application shutdown*: Rejected. Violates FR-004; crashes, forced quits, and `exit-after-launch` paths would lose games.
- *Save in `Game` when constructed*: Rejected. A new game has no values yet; the file would be a placeholder that `from_data` rejects (empty `executable`/`name` are required), and it still would not cover later edits.
- *Extend `saved_library` (the library file used for launcher games)*: Rejected. It is deliberately for launcher data that a re-scan can regenerate; manual games are the source of truth and already have a per-game file the user can back up or edit (FR-014).

## 3. Unique, Stable Identities

### Problem
`imported.new()` builds `numbers = {int(p.stem.rsplit("_", 1)[1]) for p in get_paths()}` and takes the lowest unused number. With save-on-apply the file exists right after the first Apply, which fixes the common case. Two cases remain:
- The first save failed (full or read-only data directory): no file exists, so the next game gets the same number while the first is still in the library.
- A file named like `imported_old.json` or `imported_.json` makes `int(...)` raise `ValueError`, so Add Game breaks until the file is moved. Damaged files must not do that (FR-013).

### Decision
- `imported.new(taken: Iterable[str] = ())` combines numbers from files on disk and from the IDs in `taken`, which `GameEditable.apply()` fills from the games already in the in-memory `imported` source.
- The number is parsed by a helper `_number(stem) -> int | None` that returns `None` for any stem that does not match `imported_<digits>`; those files are ignored for numbering and never opened or overwritten by `new()`.
- Removed games keep their file (`removed: true`), so their numbers stay reserved (spec User Story 3 scenario 2). Files that fail to parse still reserve their number.

### Rationale
Pure helpers (`_number`, `_next_number`) are easy to unit test without a window, and passing `taken` avoids an import cycle (`imported.py` cannot import `cartridges.sources`, which loads it dynamically).

### Alternatives Considered
- *A persistent counter file*: Rejected. Another file to keep consistent for a problem that disk plus memory solves.
- *UUID-based IDs*: Rejected. Existing games use `imported_<n>` and `collections.py` recognizes the `imported` prefix; changing the scheme risks breaking saved collections and hand-edited files.
- *Reserve the file on creation (empty placeholder)*: Rejected for the reasons in section 2.

## 4. Atomic, Reportable Save

### Decision
Rewrite `Game.save()` as: ensure `GAMES_DIR` exists, write JSON to `<id>.json.tmp` in the same directory, then `os.replace`/`Path.replace` onto the final name; on any `OSError`, remove the temporary file (itself guarded) and re-raise. `save()` keeps raising `OSError`; callers choose how to report (this mirrors `hidden_games.record` and `play_history.record`, except those swallow because they are background data).

### Rationale
- FR-012: a failure or crash mid-write can no longer truncate an existing good record, and no `.tmp` is left behind.
- FR-014: the file stays the same readable, sorted, indented JSON, so manual edits and backups still work and no migration is needed.
- The one in-repo caller that must stay quiet (`Source._save` on removal) already catches `OSError` and logs.

### Alternatives Considered
- *Swallow the error inside `save()`*: Rejected. The Apply flow needs to know in order to show the notice (FR-011).
- *`fsync` before replace*: Rejected as unnecessary for this data; atomic replace already prevents partial files from being seen, and a lost last write after power failure matches the behavior of the other stores in the app.

## 5. Reporting a Failed Save

### Decision
In `GameEditable.apply()`:
```text
try: game.save()
except OSError as e:
    log one warning (game id, reason)
    window.send_toast(_("{} could not be saved and will be lost when Cartridges closes").format(game.name))
```
The game stays in the library and works for the session. A later successful save (next Apply, or removal) writes the complete current state because `save()` always writes all properties (FR-012).

### Rationale
- The user just typed this data, so silence would hide a real loss (spec assumption), unlike background play history.
- A toast follows the project's non-blocking feedback pattern (constitution Principle IV) and the existing helpers in this module.
- Hide, remove, and undo failures stay log-only (spec assumption), keeping their toasts (such as "removed" with Undo) uncluttered.

### Alternatives Considered
- *`Adw.AlertDialog`*: Rejected. Blocking, and not warranted for a rare condition.
- *Retry in the background*: Rejected. Adds complexity; the next save already includes the data.
- *Refuse to add the game when saving fails*: Rejected. The user could not even use the game for the session; FR-011 requires it to keep working.

## 6. Collections and the Other Persisted States

### Findings and Decision
- Collections store game IDs; `_get_collections` keeps an `imported_*` ID only if its file exists. Once Apply writes the file, membership survives restarts (FR-007) with no change to `collections.py`. If the first save failed, the membership is lost after restart, which is consistent with the game itself being lost, and the user was told.
- Hidden state and last-played time already persist by game ID for all sources. `Source.scan` merges both on load for `imported` too (`hidden_games.load()` overrides the file's `hidden`, `play_history` is merged with `max`). No change needed; the quickstart verifies the combination.
- `removed` is saved by the existing `notify::removed` handler, and Undo flips it back and saves again (FR-010).

## 7. Covers

### Findings
Covers are written in `GameDetails._apply` after `game_editable.apply()` returns, under `COVERS_DIR/<game_id>.<ext>`, and are found again by ID at startup. Because the ID is now unique and the record is saved first, a cover can no longer end up attached to a duplicated ID.

### Decision
No change to cover handling. A cover write failure is outside this feature's scope (spec assumption: cover storage is unchanged). The quickstart verifies cover persistence.

## 8. Tests

### Decision
Add `tests/test_manual_games.py`, following the style of `tests/test_importer.py` (real `gi`, temporary data directory by pointing `GAMES_DIR` at a temp path, run directly with Python). Cases:
- `_number` / `_next_number`: ignores non-numeric stems, takes the lowest unused number, treats `taken` IDs as used.
- `Game.save` round trip through `imported.get_games()`: values equal after reload; atomic replace leaves no `.tmp`.
- Save failure (unwritable directory, `mkdir` failure, replace failure via monkeypatch): raises `OSError`, previous file unchanged, no temporary file.
- Two games created back to back with `taken` and no files on disk get different IDs.
- Damaged file present: other games still load and the damaged file is not modified.

The toast and the Apply flow are GTK window behavior and are verified by quickstart scenarios, not unit tests.

### Alternatives Considered
- *Drive the real Apply flow in a headless GTK test*: Rejected. It needs a display and a full application window, which the existing tests avoid.
