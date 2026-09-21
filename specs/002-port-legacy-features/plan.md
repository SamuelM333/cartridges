# Implementation Plan: Flatpak Game Source, SteamGridDB Cover Art Integration, and Preferences Menu

**Branch**: `002-port-legacy-features` | **Date**: 2026-09-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-port-legacy-features/spec.md`

## Summary

This feature ports the core configuration management, modular Flatpak game discovery, and SteamGridDB asynchronous cover art fetching from the legacy `main` branch to the modern `rewrite` branch of Cartridges. The technical approach leverages standard GNOME Libadwaita preferences controls (`Adw.PreferencesDialog`), direct bidirectional property binding with GSettings, and multi-threaded background networking to ensure seamless, native, and highly performant desktop operation with absolutely no new or custom UI concepts.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: PyGObject (GObject Introspection), Gtk 4.0, Libadwaita (Adw 1), Pillow (PIL)

**Storage**: Local files (JSON files for game metadata records under `~/.local/share/cartridges/games/` and local cover image cache under `~/.local/share/cartridges/covers/`) and persistent GSettings storage.

**Testing**: Meson-based desktop validation suites (`desktop-file-validate`, `appstreamcli validate`, schema checks) and manual scenario verification.

**Target Platform**: Linux Desktop (conforming to GNOME Shell and Flatpak sandbox environments)

**Project Type**: GNOME Desktop Application

**Performance Goals**: Preferences dialog load time under 200ms, GSettings key persistence under 50ms, stable 60 FPS visual rendering during asynchronous cover art updates.

**Constraints**: Strict compliance with official GNOME Human Interface Guidelines (HIG), strict Pyright static typing, Ruff ALL linting rule sets, and a completely emoji-free environment.

**Scale/Scope**: Purely local client-side configuration, game metadata discovery, and single-endpoint asynchronous queries.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Check | Status |
|-----------|------------------|--------|
| **I. Strict Typing & QA** | All new preferences modules, models, and controllers will be fully type-annotated and verified with `pyright` in strict mode and `ruff check`/`ruff format`. | Pass |
| **II. Modular Game Sources** | The Flatpak game scanning and launching logic will be implemented as a modular standalone class `FlatpakSource` under `cartridges/sources/flatpak.py`, decoupling presentation from system discovery. | Pass |
| **III. Blueprint UI** | The Preferences view layout will be declared 100% in GNOME Blueprint (`.blp`) format, matching the legacy layout exactly, and compiled into Meson GResource bundle structures. | Pass |
| **IV. GNOME HIG & Portal Sandboxing** | Using native `Adw.PreferencesDialog` and standard Libadwaita rows achieves perfect HIG compliance. Launching Flatpaks from within a sandbox will utilize Flatpak host execution portals. | Pass |
| **V. Resource Sandboxing & Caching** | SteamGridDB art downloads and updates are handled fully asynchronously in background worker threads, storing outputs in standard XDG caches without blocking the UI main loop. | Pass |
| **VI. Emoji-Free Standard** | Zero emoji characters are utilized in source files, Blueprint layouts, specifications, plans, checklists, or other documentation. | Pass |

## Project Structure

### Documentation (this feature)

```text
specs/002-port-legacy-features/
├── spec.md              # Feature Specification (Consolidated user stories & requirements)
├── plan.md              # Implementation Plan (This file)
├── research.md          # Technical research & decisions
├── data-model.md        # GSettings configuration & Flatpak game schemas
├── quickstart.md        # Scenario verification guide
└── checklists/
    └── requirements.md  # Specification Quality Checklist
```

### Source Code (repository root)

```text
cartridges/
├── sources/
│   ├── __init__.py      # Automatically imports and initializes flatpak.py
│   └── flatpak.py       # [NEW] Modular Flatpak Game Source subclass
├── ui/
│   ├── preferences.blp  # [NEW] GNOME Blueprint Preferences view
│   ├── preferences.py   # [NEW] Code-behind template controller for Preferences
│   ├── window.blp       # [MODIFY] Added Preferences option to main header bar menu
│   └── window.py        # [MODIFY] Bound App action menu trigger to present Preferences
├── application.py       # [MODIFY] Added 'preferences' action entries
└── config.py.in         # [MODIFY] Include GSettings preferences mapping options
```

**Structure Decision**: Single project layout matching the native `cartridges` package directories.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*(No constitution violations are present; design strictly aligns with Core Principles.)*
