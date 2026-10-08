# Implementation Plan: Main Game List View and Cover Interactions

**Branch**: `feat/005-game-list-view` | **Date**: 2026-10-08 (amended; originally 2026-10-06) | **Spec**: [specs/005-game-list-view/spec.md](file:///var/home/samuel/Projects/cartridges/specs/005-game-list-view/spec.md)

**Input**: Feature specification from `specs/005-game-list-view/spec.md`

## Summary

Restore the classic `cartridges-main` hover button design onto the main game list view cards, providing two circular buttons at the top of each cover: an action button on the top-left (Play or Info) and a three-dots menu button on the top-right (`view-more-symbolic`). The top-left button and cover click behaviors dynamically invert according to the "Cover Image Launches Game" setting (`cover-launches-game`), providing seamless launching and inspection flows. Furthermore, whenever a game launch is initiated, a dismissable in-app toast notification displays "Launched <game name>" with full internationalization/translation support.

**Amendment (2026-10-08) - Time-precise "Last Played" sorting (User Story 5, FR-014 to FR-021)**: `Game.last_played` is already a Unix timestamp with one-second precision and `_sort` already compares the full value with an alphabetical tie-break, so the sort comparator itself needs no change. The defects are that (a) launching a game from Cartridges never sets `last_played`, (b) nothing tells the sorter to re-sort after a launch, and (c) games from launcher sources (Steam, Lutris, Heroic, ...) are rebuilt from the launcher on every start, so a Cartridges-recorded time would be lost on restart. The fix adds a small source-agnostic play-history store (`cartridges/play_history.py`, persisted to `$XDG_DATA_HOME/cartridges/last-played.json`), records the launch time inside `Game.play()` before the process is spawned (and before any `exit-after-launch` quit), merges the stored time with the launcher-reported time using `max()` when sources load, and calls `sorter.changed()` after a launch so the game moves to the first position under the "Last Played" sort.

**Amendment (2026-10-08, follow-up) - Resilient recording (FR-022 to FR-025, SC-010)**: `play_history.record()` currently lets `OSError` (full disk, read-only or permission-denied data directory, failed directory creation, failed file replace) escape, and `Game.play()` calls it before spawning the process, so a storage problem stops the game from launching. The fix keeps recording first but makes it non-fatal: `record()` updates the in-memory mapping first, then attempts the write inside a handler for `OSError`, logs one warning with the reason, and removes the temporary file (itself best-effort). `Game.play()` is unchanged apart from relying on this contract: it still sets `last_played` before recording, so the session-level sort and label stay correct. No UI change, no new strings.

**Amendment (2026-10-09) - Show/hide game titles (User Story 6, FR-026 to FR-030, SC-011, SC-012)**: Each grid card ends with a `Label` bound to the game name (`cartridges/ui/game-item.blp`). The change adds a boolean GSettings key `show-game-titles` (default `true`), a switch for it on the General page of Preferences bound through the existing `_bind_switches` mechanism, and makes the card label's visibility follow the key. Three details matter: (a) a game with no cover keeps its title visible, because the placeholder cover shows only the application icon (FR-029); (b) a hidden label drops out of the accessibility tree, so `GameItem` sets an explicit accessible label to the game name from Python, because Blueprint's `accessibility { }` block cannot bind values (FR-029); (c) all cards must react live, so `GameItem` listens to `changed::show-game-titles` the same way it already does for `cover-launches-game`. No new Python module and no change to sorting or actions.

**Amendment (2026-10-08) - Full titles without truncation (User Story 7, FR-031 to FR-035, SC-013, SC-014)**: The card's `title_label` is single-line with `ellipsize: middle`, so any name wider than its grid cell is cut in the middle. The fix is declarative and local to `cartridges/ui/game-item.blp`: drop `ellipsize`, set `wrap: true`, `wrap-mode: word_char` (break between words, and inside a word only when it is wider than the card), and `justify: center` (multi-line labels default to left alignment). The label keeps its default `xalign: 0.5`. Wrapping happens at the width the grid already gives the label today, so any title that used to fit on one line still renders as the same single centered line. The cover keeps its fixed 200x300 size through `CoverLayoutManager`, and `Gtk.GridView` sizes each row to its tallest card, so covers stay top-aligned and column count is unchanged. A small template closure strips leading and trailing whitespace from the name before display, so a launcher-supplied trailing newline does not add a blank line. No settings, strings, or Python modules are added, and the show-titles logic from the previous amendment is untouched.

## Technical Context

**Language/Version**: Python 3.12+ (PyGObject / GTK 4)

**Primary Dependencies**: GTK 4, Libadwaita 1.6+, Blueprint Compiler, Meson, Ninja, GNU gettext

**Storage**: GSettings (`page.samuelm333.Cartridges`, new boolean key `show-game-titles`), XDG cache directory for cover art, per-game JSON for imported games (`$XDG_DATA_HOME/cartridges/games/`), and (new) a single play-history JSON file `$XDG_DATA_HOME/cartridges/last-played.json` mapping `game_id` to a Unix timestamp

**Testing**: Pre-commit validation hooks, Pyright static analysis in strict mode, Meson/Ninja test suites, gettext pot file extraction, unit tests for the play-history store under `tests/` (including save-failure cases)

**Target Platform**: Linux Desktop (Flatpak sandbox, GNOME 47+)

**Project Type**: Desktop Application (Libadwaita / GTK 4)

**Performance Goals**: Hover button reveal latency < 250ms; setting swap reaction < 100ms across all grid items; toast dispatch latency < 50ms; launched game reaches first position < 1s (SC-008); play-history write is a single small file, well under 10ms

**Constraints**: Flatpak sandbox isolation; zero emoji characters anywhere in code or documentation; proper gettext placeholder formatting for translators; play-history write must complete synchronously before `exit-after-launch` quits the application; corrupt or missing history file must never prevent the library from loading (SC-009); a failure to save the history must never prevent a game from launching (SC-010)

**Scale/Scope**: Refactor `cartridges/ui/game-item.blp`, `cartridges/ui/game_item.py`, `cartridges/ui/style.css`, `cartridges/ui/games.py`, and `cartridges/ui/window.py`. Title amendment touches `data/page.samuelm333.Cartridges.gschema.xml.in`, `cartridges/ui/preferences.blp`, `cartridges/ui/preferences.py`, `cartridges/ui/game-item.blp`, and `cartridges/ui/game_item.py`. Full-titles amendment touches only `cartridges/ui/game-item.blp` (label properties and closure call) and `cartridges/ui/game_item.py` (one display-title template callback). Play-history amendment adds `cartridges/play_history.py` (follow-up hardens `record()` against `OSError`) and touches `cartridges/games.py` (`Game.play`), `cartridges/sources/__init__.py` (`Source._get_games` merge), and `cartridges/ui/games.py` (`play` re-sort).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Strict Typing & QA)**: All Python methods and attributes must have complete type annotations; Pyright in strict mode and Ruff `ALL` must pass. The new `play_history` module exposes fully typed functions (`dict[str, int]`, `str`, `int`) with no `Any`. The follow-up catches the specific `OSError` rather than a blanket `Exception`, so Ruff `BLE001` and `S110` stay satisfied. -> PASS
- **Principle II (Modular Game Sources)**: Game list view UI logic remains decoupled from game discovery and source retrieval logic. Domain model `cartridges/games.py` remains free of UI widget references. The play-history merge lives in the shared `Source._get_games` wrapper, so individual source modules (`steam.py`, `lutris.py`, ...) are untouched and keep reporting only what their launcher knows. -> PASS
- **Principle III (Blueprint-Driven Declarative UI)**: Layout adjustments are written in Blueprint (`cartridges/ui/game-item.blp`) and mapped to controller classes via `Gtk.Template`. The amendment has no layout changes. -> PASS
- **Principle IV (Libadwaita Patterns & GNOME HIG)**: Buttons adhere to GNOME HIG standards using standard circular styles, symbolic icons, and Libadwaita popovers; feedback uses dismissable `Adw.Toast` via `Adw.ToastOverlay`. Re-sorting reuses the existing `Gtk.SortListModel` / `Gtk.CustomSorter`; no custom list widgets. -> PASS
- **Principle V (Resource & Asset Sandboxing)**: Assets bundled via GResource; cover image fetching remains asynchronous and sandboxed. The play-history file lives under the XDG data directory alongside existing game data. The write is a small local file done synchronously, with failures logged and tolerated; this is deliberate (it must land before `exit-after-launch` quits) and is not an external resource fetch. -> PASS
- **Principle VI (Emoji-Free Code and Documentation)**: Zero emoji characters across all markdown documents, templates, and Python sources. -> PASS
- **Branching Workflow**: Branch `feat/005-game-list-view` branched directly from `main`. -> PASS

**Post-design re-check (2026-10-09, title toggle)**: Principle III: the label and switch are declared in Blueprint, the visibility rule lives in the controller. Principle IV: uses a standard `Adw.SwitchRow` in an `Adw.PreferencesGroup` on the existing General page, and keeps names available to assistive technology. Principle I: fully typed handlers, no `Any` beyond the existing `*_args: Any` signal-handler convention. Principle VI: no emoji. No violations. The new user-visible strings (switch title and subtitle, group title) use gettext; `po/POTFILES.in` does not list the preferences files yet, so task T053 adds them before `ninja -C _build cartridges-pot` can extract the strings.

**Post-design re-check (2026-10-08, full titles)**: Principle III: the wrapping behavior is declared in Blueprint label properties; the only Python is a typed, pure display callback following the existing `Cover._content_fit` template-callback pattern. Principle IV: a standard `Gtk.Label` with wrapping and centered justification, no custom measuring or drawing; the grid keeps the stock `Gtk.GridView` layout and the existing focus indicator. Principle I: the callback is fully annotated (`str -> str`). Principle VI: no emoji. No new translatable strings. No violations.

**Post-design re-check (2026-10-08)**: Re-evaluated after writing research.md sections 6-9, data-model.md section 5, and contracts section 6. No new violations.

**Post-design re-check (follow-up)**: Re-evaluated after adding research.md section 10, the failure-handling parts of data-model.md section 5 and contracts section 6, and quickstart Scenario 11. Principle IV is served better (sandbox permission limits now degrade gracefully instead of failing the launch). No new violations.

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
│   ├── game-item.blp    # Blueprint layout: overlay buttons (top-left action, top-right menu), wrapping title label
│   ├── game_item.py     # Controller: action binding, dynamic icon swapping, hover tracking, display title
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
└── test_play_history.py # NEW (amendment): round-trip, corrupt-file, and save-failure checks
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

The full-titles amendment introduces no new strings; Pango already handles line breaking for scripts without spaces (CJK) and right-to-left text, and `justify: center` is direction-neutral.

The amendment and its follow-up introduce no new user-visible strings; the save-failure warning goes to the developer log only and is not translated.

## Complexity Tracking

*No constitution violations or unjustified architectural patterns.*
