# Contracts: Manual Game Add

**Branch**: `feat/009-manual-game-add`
**Date**: 2026-10-09

This feature exposes no network or command-line interface. Its contracts are the on-disk record, the module functions that read and write it, and the user-visible notice.

## 1. On-Disk Contract

- Path: `$XDG_DATA_HOME/cartridges/games/imported_<n>.json`, `<n>` a non-negative decimal integer.
- Format: UTF-8 JSON object with the fields in data-model.md section 1; unchanged from earlier versions.
- Compatibility: a file written by this version MUST be loadable by earlier versions, and files from earlier versions MUST load unchanged.
- The application MUST NOT delete, truncate, or rewrite a file it cannot parse or whose `version` is newer than it supports.
- No `*.tmp` file remains after a save, whether it succeeded or failed.

## 2. Function Contracts

### `Game.save() -> None` (`cartridges/games.py`)
- Writes the complete record of the game to `GAMES_DIR / f"{game_id}.json"` atomically (temporary file in the same directory, then replace).
- Creates `GAMES_DIR` if missing.
- On any `OSError`: removes the temporary file if present (cleanup errors are ignored), leaves any existing record unchanged, and re-raises the original `OSError`.
- Raises nothing else for write failures. Callers decide how to report.

### `imported.new(taken: Iterable[str] = ()) -> Game` (`cartridges/sources/imported.py`)
- Returns a game with `source = "imported"`, `added = now`, and `game_id = "imported_<n>"` where `n` follows data-model.md section 2.
- MUST NOT raise for file names that do not match `imported_<digits>.json`.
- MUST NOT open, parse, or modify existing files to compute `n`.
- Does not write to disk; the caller saves after the values are set.

### `imported.get_games() -> Generator[Game]` (unchanged)
- Yields every readable record; skips unreadable ones silently; reattaches covers by ID.

### `GameEditable.apply() -> None` (`cartridges/ui/games.py`)
For a valid form:
1. If `self.game` is `None`: create it with `imported.new(taken)` where `taken` is the `game_id` of every game in the `imported` source model, and append it to that source.
2. Copy `executable`, `name`, and `developer` onto the game.
3. If the game's `source` is `imported`: call `game.save()`.
   - On `OSError`: write one log warning containing the game ID and the reason, and call `Window.send_toast` with the notice in section 3. Do not raise.
4. Return normally in all cases so the form closes and the game is visible.

Cancel never calls `apply()` and therefore never saves.

### `Source._save(game)` (removal handler, `cartridges/sources/__init__.py`)
- Unchanged contract: calls `game.save()`, catches `OSError`, logs a warning, never notifies the user.

## 3. User-Visible Notice

| Item | Contract |
|------|----------|
| Widget | `Adw.Toast` via `Window.send_toast`, no Undo button, default timeout, dismissable |
| Text | `_("{} could not be saved and will be lost when Cartridges closes").format(game.name)` |
| Translator comment | `# Translators: {} is the name of the game that could not be saved` immediately before the call |
| When | Only when Apply on an add or an edit fails to save; at most once per Apply |
| Not shown for | Hide, unhide, remove, undo, launch, or any background save |
| Markup | Plain text (`use_markup=False`), so game names with markup characters render literally |

## 4. Non-Regression Contract

- Add Game form fields, validation, and layout are unchanged.
- Imports (`importer.import_games`, startup scan) do not touch the `imported` source.
- `hidden.json`, `last-played.json`, `library.json`, collections storage, and cover storage formats are unchanged.
- The "Launched {}" toast, hide/unhide/remove toasts and their Undo behavior are unchanged.
