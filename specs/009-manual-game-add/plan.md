# Implementation Plan: Manual Game Add

**Branch**: `feat/009-manual-game-add` | **Date**: 2026-10-09 | **Spec**: [specs/009-manual-game-add/spec.md](spec.md)

**Input**: Feature specification from `specs/009-manual-game-add/spec.md`

## Summary

Make a manually added game durable the moment the user applies it. The save path already exists (`Game.save()` writes `GAMES_DIR/<game_id>.json`, `imported.get_games()` reads `imported_*.json` back on every start, and imports skip the `imported` source), but nothing calls `save()` when a game is added or edited: the only caller is the `notify::removed` handler in `Source._track`. A game applied in the Add Game form therefore lives only in memory, and a restart loses it. Three smaller defects sit next to this and are fixed with it:

1. `imported.new()` picks the next number from files on disk only, so a second game added in the same session (first one unsaved) receives the same `game_id` as the first (FR-008).
2. `imported.new()` calls `int(...)` on every `imported_*.json` file stem, so one oddly named file raises `ValueError` and breaks Add Game (FR-013).
3. `Game.save()` truncates and rewrites the file in place and lets `OSError` escape, so a crash or full disk can leave a damaged game file (FR-012).

The change, all in existing modules, no new settings and no schema change:

- `Game.save()` becomes atomic (write a temporary file in the same directory, then replace; remove the temporary file on failure) and still raises `OSError`, so callers decide how to report it.
- `GameEditable.apply()` (`cartridges/ui/games.py`) calls `game.save()` after the editable values are copied onto an `imported` game. On `OSError` it logs one warning and shows a dismissable toast (new translatable string); the game keeps working in memory.
- `imported.new()` receives the IDs already present in the in-memory `imported` source, ignores file names that do not end in a number, and takes the lowest number unused by either.
- `Source._save` (the removal handler) keeps its log-only behavior but writes through the same atomic `save()`.

## Technical Context

**Language/Version**: Python 3.12+ (PyGObject / GTK 4)

**Primary Dependencies**: GTK 4, Libadwaita 1.6+, Blueprint Compiler, Meson, GNU gettext (no new dependencies)

**Storage**: One JSON file per manually added game at `$XDG_DATA_HOME/cartridges/games/imported_<n>.json` (existing format, no migration); covers in `$XDG_CACHE_HOME`-side `COVERS_DIR` (unchanged); `hidden.json`, `last-played.json`, and GSettings `collections` (unchanged, relied on)

**Testing**: `tests/` unit tests run directly with Python (existing pattern, real `gi`, temporary data directories); pre-commit hooks; Pyright strict; Ruff `ALL`; Meson/Ninja checks; manual quickstart in the built app

**Target Platform**: Linux desktop (Flatpak sandbox, GNOME 47+)

**Project Type**: Desktop application (Libadwaita / GTK 4)

**Performance Goals**: Save happens synchronously inside Apply and writes one small file, well under 50 ms; notice appears within 1 second of a failed save (SC-006); nothing added to startup beyond what already scans `imported_*.json`

**Constraints**: Flatpak sandbox (data directory may be read-only or restricted); no error dialogs; a failed save must never crash or block Apply; existing saved games must keep loading unchanged (no migration); no emoji

**Scale/Scope**: Touches `cartridges/games.py` (`Game.save`), `cartridges/sources/imported.py` (`new`), `cartridges/ui/games.py` (`GameEditable.apply`), and `cartridges/sources/__init__.py` (log message only if needed). New tests in `tests/test_manual_games.py`. No Blueprint, CSS, schema, or `meson.build` changes (`tests/` is not installed).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Strict Typing & QA)**: New and changed functions are fully annotated (`new(taken: Iterable[str] = ()) -> Game`, `_next_number(...) -> int`, `Game.save() -> None`). Only `OSError` is caught, never a blanket `Exception`, which keeps Ruff `BLE001` and `S110` satisfied. -> PASS
- **Principle II (Modular Game Sources)**: `imported.py` stays a source module with no GUI dependency; it gains a parameter, not a UI import. The toast lives in the UI layer (`cartridges/ui/games.py`), and the domain model (`cartridges/games.py`) only raises `OSError`. -> PASS
- **Principle III (Blueprint-Driven Declarative UI)**: No UI layout change; the only UI addition is a toast raised from the existing controller. -> PASS
- **Principle IV (Libadwaita Patterns & GNOME HIG)**: Feedback uses a dismissable `Adw.Toast` through the existing `Window.send_toast`, not a blocking dialog. Sandbox write failures degrade gracefully instead of failing the form. -> PASS
- **Principle V (Resource & Asset Sandboxing)**: Data stays under the XDG data directory next to existing game data; the write is a small synchronous local file, not an external fetch. -> PASS
- **Principle VI (Emoji-Free Code and Documentation)**: No emoji in code, strings, or documents. -> PASS
- **Branching Workflow**: Work happens on `feat/009-manual-game-add` branched from `main`. -> PASS (branch to be created before the first commit)

**Post-design re-check (2026-10-09)**: Re-evaluated after writing research.md, data-model.md, contracts, and quickstart. The decision to raise from `Game.save()` and report in the UI keeps Principle II intact. One new translatable string is added, with a translator comment. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/009-manual-game-add/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0: findings and decisions
├── data-model.md        # Phase 1: game record, ID allocation, state transitions
├── quickstart.md        # Phase 1: end-to-end validation guide
├── contracts/
│   └── persistence-contract.md  # Phase 1: file, function, and notice contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2: generated by /speckit-tasks
```

### Source Code (repository root)

```text
cartridges/
├── games.py             # Game.save(): atomic write, raises OSError
├── sources/
│   ├── __init__.py      # Source._track/_save: unchanged behavior, uses atomic save
│   └── imported.py      # new(taken): unique ID across disk and memory; tolerant of odd file names
└── ui/
    └── games.py         # GameEditable.apply(): save after apply; log + toast on failure
tests/
└── test_manual_games.py # NEW: ID allocation, atomic save, failure cases, round trip
po/
└── cartridges.pot       # Regenerated with the new notice string
```

**Structure Decision**: Persistence stays where it already lives (the `Game` model and the `imported` source module). The only layer that knows about the window and toasts, `cartridges/ui/games.py`, decides when to save and how to tell the user, mirroring how `play()`, `hide()`, and `remove()` already own their toasts.

## Translation and Internationalization Strategy

1. The notice is `_("{} could not be saved and will be lost when Cartridges closes").format(game.name)`; never an f-string or concatenation, so translators can place the name freely.
2. A `# Translators: {} is the name of the game that could not be saved` comment immediately precedes the call.
3. `cartridges/ui/games.py` is already in `po/POTFILES.in`; the gate is `ninja -C _build cartridges-pot` extracting the msgid and comment.
4. The log warning is for developers and is not translated.

## Complexity Tracking

*No constitution violations or unjustified architectural patterns.*
