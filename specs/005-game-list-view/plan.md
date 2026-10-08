# Implementation Plan: Main Game List View and Cover Interactions

**Branch**: `feat/005-game-list-view` | **Date**: 2026-10-08 (amended; originally 2026-10-06) | **Spec**: [specs/005-game-list-view/spec.md](file:///var/home/samuel/Projects/cartridges/specs/005-game-list-view/spec.md)

**Input**: Feature specification from `specs/005-game-list-view/spec.md`

## Summary

Restore the classic `cartridges-main` hover button design onto the main game list view cards, providing two circular buttons at the top of each cover: an action button on the top-left (Play or Info) and a three-dots menu button on the top-right (`view-more-symbolic`). The top-left button and cover click behaviors dynamically invert according to the "Cover Image Launches Game" setting (`cover-launches-game`), providing seamless launching and inspection flows. Furthermore, whenever a game launch is initiated, a dismissable in-app toast notification displays "Launched <game name>" with full internationalization/translation support.

**Amendment (2026-10-08) - Time-precise "Last Played" sorting (User Story 5, FR-014 to FR-021)**: `Game.last_played` is already a Unix timestamp with one-second precision and `_sort` already compares the full value with an alphabetical tie-break, so the sort comparator itself needs no change. The defects are that (a) launching a game from Cartridges never sets `last_played`, (b) nothing tells the sorter to re-sort after a launch, and (c) games from launcher sources (Steam, Lutris, Heroic, ...) are rebuilt from the launcher on every start, so a Cartridges-recorded time would be lost on restart. The fix adds a small source-agnostic play-history store (`cartridges/play_history.py`, persisted to `$XDG_DATA_HOME/cartridges/last-played.json`), records the launch time inside `Game.play()` before the process is spawned (and before any `exit-after-launch` quit), merges the stored time with the launcher-reported time using `max()` when sources load, and calls `sorter.changed()` after a launch so the game moves to the first position under the "Last Played" sort.

## Technical Context

**Language/Version**: Python 3.12+ (PyGObject / GTK 4)

**Primary Dependencies**: GTK 4, Libadwaita 1.6+, Blueprint Compiler, Meson, Ninja, GNU gettext

**Storage**: GSettings (`page.samuelm333.Cartridges`), XDG cache directory for cover art, per-game JSON for imported games (`$XDG_DATA_HOME/cartridges/games/`), and (new) a single play-history JSON file `$XDG_DATA_HOME/cartridges/last-played.json` mapping `game_id` to a Unix timestamp

**Testing**: Pre-commit validation hooks, Pyright static analysis in strict mode, Meson/Ninja test suites, gettext pot file extraction, unit tests for the play-history store under `tests/`

**Target Platform**: Linux Desktop (Flatpak sandbox, GNOME 47+)

**Project Type**: Desktop Application (Libadwaita / GTK 4)

**Performance Goals**: Hover button reveal latency < 250ms; setting swap reaction < 100ms across all grid items; toast dispatch latency < 50ms; launched game reaches first position < 1s (SC-008); play-history write is a single small file, well under 10ms

**Constraints**: Flatpak sandbox isolation; zero emoji characters anywhere in code or documentation; proper gettext placeholder formatting for translators; play-history write must complete synchronously before `exit-after-launch` quits the application; corrupt or missing history file must never prevent the library from loading (SC-009)

**Scale/Scope**: Refactor `cartridges/ui/game-item.blp`, `cartridges/ui/game_item.py`, `cartridges/ui/style.css`, `cartridges/ui/games.py`, and `cartridges/ui/window.py`. Amendment adds `cartridges/play_history.py` and touches `cartridges/games.py` (`Game.play`), `cartridges/sources/__init__.py` (`Source._get_games` merge), and `cartridges/ui/games.py` (`play` re-sort).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Strict Typing & QA)**: All Python methods and attributes must have complete type annotations; Pyright in strict mode and Ruff `ALL` must pass. The new `play_history` module exposes fully typed functions (`dict[str, int]`, `str`, `int`) with no `Any`. -> PASS
- **Principle II (Modular Game Sources)**: Game list view UI logic remains decoupled from game discovery and source retrieval logic. Domain model `cartridges/games.py` remains free of UI widget references. The play-history merge lives in the shared `Source._get_games` wrapper, so individual source modules (`steam.py`, `lutris.py`, ...) are untouched and keep reporting only what their launcher knows. -> PASS
- **Principle III (Blueprint-Driven Declarative UI)**: Layout adjustments are written in Blueprint (`cartridges/ui/game-item.blp`) and mapped to controller classes via `Gtk.Template`. The amendment has no layout changes. -> PASS
- **Principle IV (Libadwaita Patterns & GNOME HIG)**: Buttons adhere to GNOME HIG standards using standard circular styles, symbolic icons, and Libadwaita popovers; feedback uses dismissable `Adw.Toast` via `Adw.ToastOverlay`. Re-sorting reuses the existing `Gtk.SortListModel` / `Gtk.CustomSorter`; no custom list widgets. -> PASS
- **Principle V (Resource & Asset Sandboxing)**: Assets bundled via GResource; cover image fetching remains asynchronous and sandboxed. The play-history file lives under the XDG data directory alongside existing game data. The write is a small local file done synchronously; this is deliberate (it must land before `exit-after-launch` quits) and is not an external resource fetch. -> PASS
- **Principle VI (Emoji-Free Code and Documentation)**: Zero emoji characters across all markdown documents, templates, and Python sources. -> PASS
- **Branching Workflow**: Branch `feat/005-game-list-view` branched directly from `main`. -> PASS

**Post-design re-check (2026-10-08)**: Re-evaluated after writing research.md sections 6-9, data-model.md section 5, and contracts section 6. No new violations.

## Project Structure

### Documentation (this feature)

```text
specs/005-game-list-view/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0: Technical research and decisions
├── data-model.md        # Phase 1: Entities, settings, and widget states
├── quickstart.md        # Phase 1: End-to-end verification and run guide
├── contracts/
│   └── ui-contracts.md  # Phase 1: Widget template, action, and play-history contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2: Tasks (generated by /speckit-tasks)
```

### Source Code (repository root)

```text
cartridges/
├── games.py             # Domain model: Game.play() records last_played before spawning (amendment)
├── play_history.py      # NEW (amendment): load/record Cartridges-recorded launch times
├── sources/
│   └── __init__.py      # Source._get_games merges play history with launcher time via max() (amendment)
├── ui/
│   ├── game-item.blp    # Blueprint layout: overlay buttons (top-left action, top-right menu)
│   ├── game_item.py     # Controller: action binding, dynamic icon swapping, hover tracking
│   ├── style.css        # CSS styles: hover transitions and button transforms
│   ├── games.py         # UI actions: centralized play(game) helper with toast and re-sort
│   ├── window.blp       # GridView container, toast overlay, and empty view stacks
│   ├── window.py        # Window controller and grid activation handling
│   └── preferences.blp  # Settings UI: "Cover Image Launches Game" switch row
data/
└── page.samuelm333.Cartridges.gschema.xml.in  # GSettings schema definition
po/
├── POTFILES.in          # Translatable source file manifest (includes cartridges/ui/games.py)
└── cartridges.pot       # Translation catalog template
tests/
└── test_play_history.py # NEW (amendment): round-trip, corrupt-file, and max-merge checks
```

**Structure Decision**: The feature is strictly contained within the UI layer (`cartridges/ui/`) of the desktop application. The launch toast notification is dispatched via `_window().send_toast(...)` inside `cartridges/ui/games.py`, keeping domain logic (`cartridges/games.py`) cleanly separated from the UI presentation layer. For the amendment, recording and persisting the launch time is domain logic and lives in `cartridges/games.py` and `cartridges/play_history.py`; only the re-sort trigger lives in the UI layer, because the sorter is a UI-layer object.

## Translation and Internationalization Strategy

To ensure first-class localization across all supported languages, the implementation strictly adheres to the following translation principles:

1. **Gettext Placeholder Formatting**:
   - The notification string MUST be defined as `_("Launched {}").format(game.name)`.
   - Never use Python f-strings (e.g. `f"Launched {game.name}"`) because f-strings are evaluated at runtime prior to gettext catalog lookup, preventing translation.
   - Never use string concatenation (e.g. `_("Launched ") + game.name`), which forces English-specific Subject-Verb-Object word ordering and prevents grammatically correct translations in languages requiring postpositions or alternative sentence structures (e.g., Japanese, Korean, Turkish, German).

2. **Translator Context Comments**:
   - An explicit translator comment `# Translators: {} is the name of the game that was launched` MUST precede the gettext call in `cartridges/ui/games.py`.
   - The Meson/Ninja `cartridges-pot` target uses `preset: 'glib'` which automatically extracts comments with the `Translators:` prefix into `po/cartridges.pot`.

3. **Bidirectional (BiDi) Text & Script Handling**:
   - Game titles can originate from any language or script (Latin, Cyrillic, CJK, Arabic, Hebrew). GTK 4 and Libadwaita Pango rendering handles bidirectional isolates automatically when rendering `Adw.Toast` title labels, ensuring mixed LTR game names within RTL desktop environments do not cause punctuation inversion.

4. **Catalog Verification Gate**:
   - The implementation phase MUST run `ninja -C _build cartridges-pot` to verify that `po/cartridges.pot` extracts the new msgid and its associated translator comment cleanly without syntax warnings or errors.

The amendment introduces no new user-visible strings.

## Complexity Tracking

*No constitution violations or unjustified architectural patterns.*
