# Implementation Plan: Game Import

**Branch**: `feat/008-game-import` | **Date**: 2026-10-08 (amended 2026-10-09) | **Spec**: [specs/008-game-import/spec.md](spec.md)

**Input**: Feature specification from `specs/008-game-import/spec.md`

## Summary

Add an on-demand **Import Now** action to the Import page of Preferences, make every Import setting actually affect what is imported, and make hiding a game last across restarts (amendment 2026-10-09).

Today all sources are scanned once, synchronously, in `Application.do_startup` via `sources.load()`, and there is no way to re-scan. The change adds:

- A new module `cartridges/importer.py` with an `ImportState` GObject (`running` property), a pure `reconcile()` function, and an `import_games()` coroutine. The coroutine re-scans each source except manually added games on the GLib main loop, yielding between batches, and applies the result to each `Source` in place by `game_id`. Existing `Game` objects are kept, so in-session edits and hidden state survive. New games are appended and uninstalled games are removed.
- An `app.import` action that runs the coroutine, is disabled while it runs, sends a result toast, and fetches SteamGridDB covers for new games.
- A new first group on the Import page with an "Import Now" row (button and spinner stack, same pattern as "Update Covers").
- A new module `cartridges/hidden_games.py` that stores the user's hide and unhide choices by `game_id` in `$XDG_DATA_HOME/cartridges/hidden.json`, modelled on `play_history.py`. `Source.scan()` applies it to every scanned game, and a `notify::hidden` handler on each game records changes, including Undo. This closes G-4 and FR-019, FR-020.
- Removed games: `reconcile()` treats an existing launcher game with `removed` set like an uninstalled one and takes the freshly scanned object as a new game, so any import brings it back and counts it as new (FR-021). Removing a manually added game is saved to its game file by a `notify::removed` handler, so it stays removed (FR-022).

The settings changes:

- `auto-import` is replaced by `import-on-startup` (default `true`), which gates the startup scan.
- `remove-missing` is removed.
- Every source honors its enable switch (checked centrally in `Source`).
- Steam, Lutris, Heroic, itch and Legendary honor a user-set install location through a shared `location()` helper. When the user hasn't set one, auto-detection continues as today, so there is no regression.
- Lutris and Heroic honor their sub-options.

## Technical Context

**Language/Version**: Python 3.12+ (PyGObject / GTK 4)

**Primary Dependencies**: GTK 4, Libadwaita 1.6+ (`Adw.Spinner`), PyGObject asyncio integration (`Gio.Application.create_asyncio_task`), Blueprint Compiler, Meson, Ninja, GNU gettext

**Storage**: GSettings (`page.samuelm333.Cartridges`): new key `import-on-startup`, removed keys `auto-import` and `remove-missing`, existing source keys now read. One new file, `$XDG_DATA_HOME/cartridges/hidden.json` (`{game_id: bool}`), written atomically like `last-played.json`. Launcher games themselves remain unpersisted; manually added games stay in `$XDG_DATA_HOME/cartridges/games/`.

**Testing**: Pre-commit hooks, Pyright strict, Ruff, `ninja -C _build test`. New `tests/test_importer.py` covers reconciliation invariants and location resolution, using the stubbed-package style of `tests/test_play_history.py`. `tests/test_hidden_games.py` covers loading, recording and damaged files. `tests/test_settings.py` is updated for the schema change. Manual scenarios are in [quickstart.md](quickstart.md).

**Target Platform**: Linux desktop (Flatpak sandbox, GNOME 47+)

**Project Type**: Desktop application (Libadwaita / GTK 4)

**Performance Goals**:
- Import Now finishes in under 10 s for 500 games (SC-002).
- No main-loop stall longer than 250 ms during Import Now (SC-002).
- Re-sorting and filtering happen once per source, not once per game.

**Constraints**:
- Sources that touch `Gtk.IconTheme` or schedule asyncio tasks must stay on the main thread (research section 4).
- The startup scan stays synchronous and gives identical results with default settings (SC-005).
- Closing Preferences must not cancel an import.
- No emoji.

**Scale/Scope**:
- New: `cartridges/importer.py`, `cartridges/hidden_games.py`, `tests/test_importer.py`, `tests/test_hidden_games.py`.
- Changed: `cartridges/sources/__init__.py`, `steam.py`, `lutris.py`, `heroic.py`, `itch.py`, `legendary.py`, `flatpak.py`, `cartridges/application.py`, `cartridges/ui/preferences.blp`, `cartridges/ui/preferences.py` (also drops its manual `game.save()` calls in Remove All and Undo, now covered by the handler), `data/page.samuelm333.Cartridges.gschema.xml.in`, `tests/test_settings.py`, and `cartridges/meson.build` (install the new modules).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Strict Typing & QA)**: New code is fully typed: `ImportState`, `Reconciliation` (`NamedTuple`), `reconcile()`, `import_games() -> list[Game]`, `location() -> Path`, and `hidden_games.load()` / `record()`. Failures are caught as `OSError`, `sqlite3.Error`, `JSONDecodeError` and `UnicodeDecodeError`, not a blanket `Exception`. -> PASS
- **Principle II (Modular Game Sources)**: Source modules keep a single job: discovery. Each reads only its own settings, following the precedent `flatpak.py` already sets, and has no GUI dependencies. The enable check and location resolution are shared helpers in `sources/__init__.py`. Hidden-state storage lives outside the `sources` package, in `hidden_games.py`, for the same auto-loading reason; sources never import it, only `Source` does. Run state and reconciliation live outside the `sources` package, in `importer.py`, because any module in that package would be auto-loaded as a source. -> PASS
- **Principle III (Blueprint-Driven Declarative UI)**: The new row, stack, button and spinner are declared in `preferences.blp`. The controller only binds `running` to the stack's visible child. -> PASS
- **Principle IV (Libadwaita, HIG)**:
  - Uses `Adw.PreferencesGroup`, `Adw.ActionRow` and an `Adw.Spinner` embedded in the row (IV.5).
  - The result goes to an `Adw.Toast`, not a dialog.
  - The trigger is a `Gio` action, `app.import` (IV.6).
  - Location reads stay within the host paths the sandbox already exposes. -> PASS
- **Principle V (Resource Sandboxing)**:
  - `hidden.json` lives in the XDG data directory next to `last-played.json` and is written through a temporary file and an atomic rename, so a crash cannot leave a half-written file.
  - Covers for new games are fetched asynchronously through the existing SteamGridDB path.
  - The scan yields to the main loop, so the GTK main thread is not blocked for long. -> PASS
- **Principle VI (Emoji-Free)**: No emoji in code or docs. -> PASS
- **Branching Workflow**: Implementation goes on `feat/008-game-import`, branched from `main`. (The spec was written while on `main`; create the branch before implementing.) -> PASS

**Post-design re-check (2026-10-09, after the amendment)**: Re-evaluated with `hidden_games.py` and the changed reconciliation rule. No violations. The new module follows the `play_history.py` precedent exactly (module-level cache, tolerant loading, best-effort saving), so it adds no new pattern.

**Post-design re-check (2026-10-08)**: Re-evaluated after writing research.md, data-model.md, contracts/ui-contracts.md and quickstart.md. No violations. One recorded risk: Steam's single `appinfo.vdf` parse may exceed the 250 ms stall budget on very large libraries. Research section 4 gives a narrow follow-up (move only that parse to a thread) to apply if Quickstart Scenario 7 measures it over budget.

## Project Structure

### Documentation (this feature)

```text
specs/008-game-import/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0: decisions and rationale
├── data-model.md        # Phase 1: Source, Game ownership, import run, settings
├── quickstart.md        # Phase 1: build, automated checks, manual scenarios
├── contracts/
│   └── ui-contracts.md  # Phase 1: Preferences layout, app.import, module APIs
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 (generated by /speckit-tasks)
```

### Source Code (repository root)

```text
cartridges/
├── application.py       # app.import action, toast, SGDB cover fetch for new games (refactor to accept a game list)
├── importer.py          # NEW: ImportState, reconcile() (removed launcher games return), import_games()
├── hidden_games.py      # NEW: persisted hide/unhide choices, keyed by game_id
├── meson.build          # install importer.py and hidden_games.py
├── sources/
│   ├── __init__.py      # Source.scan() (also applies hidden state and tracks hide/remove changes), Source.replace_games(), enable check, location(), import-on-startup gate, sqlite3.Error handling
│   ├── steam.py         # location("steam-location", ...)
│   ├── lutris.py        # location("lutris-location", ...); runner filter honors lutris-import-steam / -flatpak
│   ├── heroic.py        # location("heroic-location", ...); store classes gated by heroic-import-*
│   ├── itch.py          # location("itch-location", ...)
│   ├── legendary.py     # location("legendary-location", ...)
│   └── flatpak.py       # drop its own enable check
└── ui/
    ├── preferences.blp  # new Import Now group; import_on_startup_switch; remove remove_missing_switch
    └── preferences.py   # template children, _bind_switches keys, bind importer.state.running to stack; drop manual game.save() in Remove All / Undo
data/
└── page.samuelm333.Cartridges.gschema.xml.in  # add import-on-startup; remove auto-import, remove-missing
tests/
├── test_importer.py     # NEW: reconcile invariants (incl. removed games return), location() rules
├── test_hidden_games.py # NEW: load, record, damaged file, save failure
└── test_settings.py     # expect import-on-startup, not remove-missing
```

**Structure Decision**: The single-project layout is unchanged. Import orchestration goes in a new top-level module, `cartridges/importer.py`, next to the existing `play_history.py`. Discovery stays in `cartridges/sources/`. UI changes are limited to the Preferences template and its controller. The application owns the action, so the import outlives the Preferences dialog. Persisted hide state is a sibling of `play_history.py`.

**Behavior summary for removed and hidden games** (spec FR-019 to FR-023):

| Action | Launcher game | Manually added game |
|--------|---------------|---------------------|
| Hide / unhide | Saved in `hidden.json`; survives restart and import | Same |
| Remove | In memory only; next import (startup or Import Now) brings it back as a new game, still hidden if it was hidden | Saved in its game file; never brought back |
| Undo of either | Goes through the same handlers, so it is saved the same way | Same |

## Translation and Internationalization

New user-visible strings, all through gettext:

| String | File | Notes |
|--------|------|-------|
| "Import Now" | `preferences.blp` | Row title |
| "Scan your sources for new and uninstalled games" | `preferences.blp` | Row subtitle |
| "Import" | `preferences.blp` | Button label |
| "Import Games on Startup" | `preferences.blp` | Replaces "Import Games Automatically" |
| "{} new game imported" / "{} new games imported" | `application.py` | `ngettext`, with a `Translators:` comment explaining `{}` |
| "No new games found" | `application.py` | |

All three files are already in `po/POTFILES.in`. "Remove Uninstalled Games" and "Import Games Automatically" leave the catalog. Verify with `ninja -C _build cartridges-pot`.

## Complexity Tracking

*No constitution violations or unjustified architectural patterns.*
