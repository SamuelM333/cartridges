# Implementation Plan: Flatpak Game Source, SteamGridDB Cover Art Integration, and Preferences Menu

**Branch**: `002-port-legacy-features` | **Date**: 2026-09-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-port-legacy-features/spec.md`

## Summary

This feature ports configuration management, modular Flatpak game discovery, and SteamGridDB asynchronous cover art fetching from the legacy `main` branch to the modern `rewrite` branch of Cartridges. The technical approach leverages standard GNOME Libadwaita preferences controls (`Adw.PreferencesDialog`), direct bidirectional property binding with GSettings, multi-threaded background networking, real-time visual progress reporting under "Update Covers", and automatic background cover fetching on startup, with strict adherence to the GNOME Human Interface Guidelines and zero new or custom UI concepts.

## Technical Context

**Language/Version**: Python 3.13+ (Python 3.14 in container)

**Primary Dependencies**: PyGObject (GObject Introspection), Gtk 4.0, Libadwaita (Adw 1), Pillow (PIL)

**Storage**: Local files (JSON files for game metadata records under `~/.local/share/cartridges/games/` and local cover image cache under `~/.local/share/cartridges/covers/`) and persistent GSettings storage (`page.samuelm333.Cartridges`).

**Testing**: Meson-based desktop validation suites (`desktop-file-validate`, `appstreamcli validate`, schema checks), blueprint compiler (`blueprint-compiler compile`), ruff (`ALL`), pyright strict type checking, and manual scenario verification.

**Target Platform**: Linux Desktop (conforming to GNOME Shell and Flatpak sandbox environments)

**Project Type**: GNOME Desktop Application

**Performance Goals**: Preferences dialog load time under 200ms, GSettings key persistence under 50ms, stable 60 FPS visual rendering during asynchronous cover art updates.

**Constraints**: Strict compliance with official GNOME Human Interface Guidelines (HIG), strict Pyright static typing, Ruff ALL linting rule sets, and a completely emoji-free codebase and documentation standard.

**Scale/Scope**: Purely local client-side configuration, game metadata discovery, real-time UI progress feedback, and single-endpoint asynchronous queries.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Check | Status |
|-----------|------------------|--------|
| **I. Strict Typing & QA** | All preferences modules, models, utilities, and controllers are fully type-annotated and pass `pyright` strict typing and `ruff check`/`ruff format`. Standard logging initialized via `logging.basicConfig()` in `__main__.py`. | Pass |
| **II. Modular Game Sources** | The Flatpak game scanning and launching logic is implemented as a modular standalone class `FlatpakSource` under `cartridges/sources/flatpak.py`, decoupling presentation from system discovery. | Pass |
| **III. Blueprint UI** | The Preferences view and Cover Picker layouts are declared 100% in GNOME Blueprint (`.blp`) format, matching the legacy layout exactly, and compiled into Meson GResource bundle structures. | Pass |
| **IV. GNOME HIG & Portal Sandboxing** | Using native `Adw.PreferencesDialog` and standard Libadwaita rows achieves perfect HIG compliance. Real-time progress displays cleanly within `Adw.ActionRow` and `Gtk.ProgressBar`. Launching Flatpaks utilizes standard host command portals. | Pass |
| **V. Resource Sandboxing & Caching** | SteamGridDB art downloads and updates are handled fully asynchronously in background worker threads without blocking the GTK UI main loop, caching results under `~/.local/share/cartridges/covers/`. | Pass |
| **VI. Emoji-Free Standard** | Zero emoji characters are utilized across all source files, Blueprint layouts, specifications, plans, checklists, or other documentation. | Pass |

## Project Structure

### Documentation (this feature)

```text
specs/002-port-legacy-features/
├── spec.md              # Feature Specification (Consolidated user stories & requirements)
├── plan.md              # Implementation Plan (This file)
├── research.md          # Technical research & decisions (including progress UI & logging)
├── data-model.md        # GSettings configuration, Flatpak model, and progress state
├── quickstart.md        # Scenario verification guide
├── contracts/           # Interface contracts
│   ├── gsettings.md     # GSettings schema configuration contract
│   ├── steamgriddb.md   # SteamGridDB client interface contract
│   └── source.md        # Modular Game Source contract
└── checklists/
    └── requirements.md  # Specification Quality Checklist
```

### Source Code (repository root)

```text
cartridges/
├── __main__.py          # [MODIFY] Standard logging configuration initialization
├── application.py       # [MODIFY] Added 'preferences' action and startup SGDB auto-fetch
├── games.py             # [MODIFY] Track original post-import cover artwork for reset
├── meson.build          # [MODIFY] Install 'sources', 'ui', and 'utils' subdirectories
├── sources/
│   ├── __init__.py      # Automatically imports and initializes flatpak.py
│   └── flatpak.py       # Modular Flatpak Game Source subclass
├── ui/
│   ├── cover_picker.blp # Cover picker dialog Blueprint layout
│   ├── cover_picker.py  # Cover picker dialog controller (capped at 10 results, supports game_name)
│   ├── game_details.py  # Staged cover editing controller, local picker, SGDB picker with title validation, delete, apply/cancel
│   ├── game-details.blp # Blueprint layout with legacy cover overlay buttons (trash, folder, globe) in Edit mode
│   ├── preferences.blp  # GNOME Blueprint Preferences view with SGDB progress row and dismissable status banner
│   ├── preferences.py   # Code-behind template controller with real-time progress and dismissable banner
│   ├── window.blp       # Preferences option in main header bar menu
│   └── window.py        # Bound App action menu trigger to present Preferences
└── utils/
    ├── __init__.py      # [NEW] Utils package marker
    └── steamgriddb.py   # [NEW] SteamGridDB API client and cover image processor
```

**Structure Decision**: Single project layout matching native `cartridges` package directories.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*(No constitution violations are present; design strictly aligns with Core Principles.)*
