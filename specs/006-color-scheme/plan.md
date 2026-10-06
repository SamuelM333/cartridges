# Implementation Plan: System Color Scheme Synchronization

**Branch**: `feat/006-color-scheme` | **Date**: 2026-10-06 | **Spec**: [spec.md](file:///var/home/samuel/Projects/cartridges/specs/006-color-scheme/spec.md)

**Input**: Feature specification from `/specs/006-color-scheme/spec.md`

## Summary

Enable automatic synchronization with the host operating system's color scheme (light and dark) by setting Libadwaita's `Adw.StyleManager` to `Adw.ColorScheme.DEFAULT` during application startup, replacing the hardcoded `Adw.ColorScheme.PREFER_DARK`. Keep the Preferences dialog clean by omitting manual theme choice toggles, ensuring seamless and native desktop integration.

## Technical Context

**Language/Version**: Python 3.12+ (PyGObject, GTK 4, Libadwaita 1)

**Primary Dependencies**:
- `gi.repository.Adw` (Libadwaita `StyleManager`, `ColorScheme`)
- `gi.repository.Gtk` (GTK 4 widgets)

**Storage**: None required (theme is delegated to host environment via `Adw.StyleManager`)

**Testing**: Meson build & test suite (`ninja -C _build test`), Blueprint template compilation, Pyright static analysis in strict mode (`uv run pyright`), Ruff linting (`uv run ruff check`)

**Target Platform**: Linux Desktop (Flatpak / Host, GNOME 47+)

**Project Type**: Desktop application (GTK 4 / Libadwaita)

**Performance Goals**: Instantaneous color scheme transition (< 100ms) without visual flicker or main thread blockage

**Constraints**:
- Strict type checking (Pyright strict mode) with zero untyped variables
- Full emoji-free compliance across code, comments, blueprints, and documentation (Principle VI)
- Blueprint-driven declarative UI templates (`.blp`)
- Canonical reference patterns conforming to `adwaita-1-demo` (Principle IV)

**Scale/Scope**:
- 1 application startup update (`cartridges/application.py`)
- Clean Blueprint template without appearance group (`cartridges/ui/preferences.blp`)
- Clean controller without appearance bindings (`cartridges/ui/preferences.py`)
- Clean GSettings schema without `color-scheme` key (`data/page.samuelm333.Cartridges.gschema.xml.in`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Strict Typing, Code Formatting & Quality Assurance**: PASS. All code passes Pyright strict mode and Ruff checks executed via `uv run`.
- **Principle II: Modular Game Sources**: PASS. Game sources remain decoupled and unmodified.
- **Principle III: Blueprint-Driven Declarative UI**: PASS. Preferences layout remains strictly declarative in `preferences.blp`.
- **Principle IV: Libadwaita Patterns, GNOME HIG & Desktop Integration**: PASS. Respects GNOME HIG by delegating color scheme to the desktop portal using `Adw.ColorScheme.DEFAULT`.
- **Principle V: Resource and Asset Sandboxing**: PASS. No unnecessary storage keys or unsandboxed resources.
- **Principle VI: Emoji-Free Code and Documentation**: PASS. Zero emojis across all files.

## Project Structure

### Documentation (this feature)

```text
specs/006-color-scheme/
├── plan.md              # Implementation plan (/speckit-plan)
├── research.md          # Architectural decisions & research (/speckit-plan)
├── data-model.md        # Entities, validation rules, state transitions (/speckit-plan)
├── quickstart.md        # Step-by-step verification guide (/speckit-plan)
├── contracts/           # UI and Settings contracts (/speckit-plan)
│   └── color-scheme-contract.md
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Execution task breakdown (/speckit-tasks)
```

### Source Code Touchpoints

```text
cartridges/
├── application.py       # Set style_manager.props.color_scheme = Adw.ColorScheme.DEFAULT in do_startup
├── ui/
│   ├── preferences.blp  # Ensure general_page does not contain appearance_group
│   └── preferences.py   # Ensure no color_scheme_group template child or binding
data/
└── page.samuelm333.Cartridges.gschema.xml.in # Ensure no color-scheme key
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
