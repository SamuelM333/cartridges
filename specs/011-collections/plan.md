# Implementation Plan: Collections

**Branch**: `feat/011-collections` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/011-collections/spec.md`

## Summary

Collections already work (spec user stories 1 to 3), so most of this plan protects that behavior with tests. The one change is the new preference **Hidden games show in Collections** (user story 4): a GSettings boolean (off by default) shown as a switch in Preferences > General > Behavior with the subtitle "Useful for hiding launchers and tools". The main window's grid filter changes so that, while Show Hidden Games is off and a collection is open, hidden games are listed as well when the preference is on (Show Hidden Games itself keeps listing only hidden games). That is done by wrapping the existing hidden-games filter in a `Gtk.AnyFilter` next to one small new filter, `HiddenInCollectionFilter`, which has three inputs (the open collection, the preference, and whether the view lists only hidden games), so the grid still updates live when a game is hidden or a setting changes. A prototype of this filter tree confirmed the live updates before the plan was written (see [research.md](research.md) R1).

## Technical Context

**Language/Version**: Python 3.13+ (`requires-python >= 3.13`)

**Primary Dependencies**: PyGObject with GTK 4 and Libadwaita 1 (`Gtk.Filter`, `Gtk.AnyFilter`, `Adw.SwitchRow`), GSettings. No new dependencies.

**Storage**: One new GSettings boolean, `hidden-games-in-collections`. Collections themselves stay in the existing `collections` key (`aa{sv}`); the format does not change.

**Testing**: Script-style tests registered in `tests/meson.build` (constitution Quality Gates item 5), using the package-stub pattern of `tests/test_importer.py`. GTK filters and list models run headless, so no display is needed. CI runs them.

**Target Platform**: Linux desktop, Flatpak first; builds for the other platforms keep working since nothing here is platform specific.

**Project Type**: Desktop application (GNOME).

**Performance Goals**: The preference or the open collection changing re-runs the grid filter once; for libraries of thousands of games this is the same cost as typing in the search box.

**Constraints**: Off by default and no change in behavior while off (SC-004); takes effect without a restart (FR-013); translatable strings only in files already listed in `po/POTFILES.in`.

**Scale/Scope**: 1 new schema key, 1 new filter class, 1 new window property, 1 new switch row, 1 new test file, small edits to about 6 existing files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Checked against constitution v3.0.0.

| Principle or rule | Status | How the design complies |
|-------------------|--------|-------------------------|
| I. Strict typing and QA | Pass | The new filter class and window property are fully annotated, with no `Any`; Pyright strict, Ruff, and the pre-commit gates run before completion. |
| II. Modular game sources | Pass (N/A) | No source changes. |
| III. Blueprint-driven UI | Pass | The filter tree and the switch row are declared in `window.blp` and `preferences.blp`; Python only defines the filter class and the property. |
| IV. Libadwaita and HIG | Pass | A standard `Adw.SwitchRow` in the existing Behavior group. The requested text is the row subtitle, so it is always visible and reaches touch and keyboard users; this is the pattern the neighboring rows use. |
| V. Resource and asset sandboxing | Pass (N/A) | No files, no network. |
| VI. Restrained emoji use | Pass | No emoji added. The 21 collection icons are functional content and stay as they are. |
| VII. No silent failures | Pass | No exception handlers are added or changed; the existing handler for a damaged stored collection already logs a warning. |
| Quality Gates: tests and CI | Pass | `tests/test_collections.py` is added to `tests/meson.build`, so `ninja -C _build test` and CI run it. |
| Quality Gates: real example output | Pass | The contracts and quickstart contain no example output. |
| Workflow: commit and PR | Pass | Commits use `uv run git commit` with an attribution trailer, and the implementing agent opens the pull request. |

**Post-design re-check (after Phase 1)**: Pass. The design added no handlers, strings outside listed files, or dependencies.

## Project Structure

### Documentation (this feature)

```text
specs/011-collections/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── preferences-ui.md
│   └── visibility-rules.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks (not created here)
```

### Source Code (repository root)

```text
data/page.samuelm333.Cartridges.gschema.xml.in  # + hidden-games-in-collections (b, default false)
cartridges/
└── ui/
    ├── collections.py                          # + HiddenInCollectionFilter
    ├── window.py                               # + hidden_in_collections property, bound to the setting
    ├── window.blp                              # grid filter: AnyFilter(hidden BoolFilter, HiddenInCollectionFilter)
    ├── preferences.blp                         # + hidden_games_in_collections_switch in behavior_group
    └── preferences.py                          # + Template.Child and the key in _bind_switches
tests/
├── test_collections.py                         # NEW: persistence baseline and visibility rules
├── test_settings.py                            # + key and default
└── meson.build                                 # + test_collections
```

**Structure Decision**: Single-project desktop app. The filter sits next to `CollectionFilter` in `cartridges/ui/collections.py`, because the two always work together and that module is already imported by `window.py`. The Window owns the property, bound one way from the setting (`Gio.SettingsBindFlags.GET`), so only Preferences writes the setting. No data-layer module changes: the preference is pure view logic and `cartridges/collections.py` stays as it is.

### Key interfaces (shape only)

```text
HiddenInCollectionFilter(Gtk.Filter)
  collection: Collection | None    # the open collection, bound from Window.collection
  enabled: bool                    # the preference, bound from Window.hidden_in_collections
  hidden_only: bool                # Show Hidden Games, bound from Window.show_hidden
  do_match(item) -> bool           # True for every item when collection is set, enabled, and not hidden_only
  do_get_strictness()              # ALL when it matches, NONE otherwise
  (emits Gtk.Filter.changed when either property changes)

Window.hidden_in_collections: bool   # GObject property, SETTINGS "hidden-games-in-collections" -> property (GET)
```

## Complexity Tracking

No constitution violations to justify.
