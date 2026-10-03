# Implementation Plan: SteamGridDB Cover Picker and Credentials UX

**Branch**: `004-steamgriddb-picker` | **Date**: 2026-10-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-steamgriddb-picker/spec.md`

## Summary

This feature enhances the SteamGridDB cover art selection and authentication workflow in Cartridges. An architectural assessment confirms that core parts of the user experience (dialog sizing, 2:3 aspect ratio thumbnail presentation, empty Title validation with error styling, and cover staging download spinners) are already fully implemented. The remaining work focuses on:
1. Upgrading the SteamGridDB API key input in Preferences to `Adw.PasswordEntryRow` with a fixed set amount of masked characters (e.g. 20 dots) fitting the input field, automatic focus loss when clicking away, and an eye-icon toggle to reveal the actual plaintext key.
2. Enhancing `CoverPicker` with a `Gtk.Stack` featuring an initial centered `Adw.Spinner` and empty status page.
3. Adding a horizontally centered `Adw.Spinner` at the bottom of the candidate list for progressive batch loading.
4. Implementing local thumbnail caching under `$XDG_CACHE_HOME/cartridges/previews/` with TTL expiration pruning and automatic cleanup on application exit.

## Current Implementation Status

| User Story | Scope / Component | Status | Implementation Details |
|------------|-------------------|--------|------------------------|
| **US1** | API key masking, fixed length & focus loss | **Done** | `Adw.PasswordEntryRow` with 20-character fixed mask and click-away focus loss in `preferences.py`. |
| **US2 (part a)** | Dialog sizing (>= 760x520) | **Done** | `cover_picker.blp` sets `content-width: 800; content-height: 580;`. |
| **US2 (part b)** | 2:3 aspect ratio thumbnails | **Done** | `cover_picker.py` sets `140x210` with `Gtk.ContentFit.CONTAIN`. |
| **US2 (part c)** | Initial centered spinner & empty state | **To Do** | Implement `Gtk.Stack` with `loading`, `empty`, and `results` in `cover_picker.blp` and `cover_picker.py`. |
| **US3** | Centered bottom spinner for batches | **To Do** | Add `bottom_spinner: Adw.Spinner` centered below `flowbox` in `cover_picker.blp` and wire in `cover_picker.py`. |
| **US4** | Thumbnail caching & lifecycle cleanup | **To Do** | Implement cache storage, SHA-256 keys, TTL pruning, and exit cleanup in `steamgriddb.py` and `application.py`. |
| **US5** | Search triggering & title validation | **Done** | Implemented in `game_details.py` (lines 273-277: validates title, adds `"error"` CSS class, focuses entry). |
| **US6** | Cover staging download spinner | **Done** | Implemented in `game_details.py` (lines 328-372: `cover_loading` GObject property with centered spinner). |

## Technical Context

**Language/Version**: Python 3.13+ (Python 3.14 in container)

**Primary Dependencies**: PyGObject (GObject Introspection), Gtk 4.0, Libadwaita (Adw 1), Pillow (PIL)

**Storage**: Local files: GSettings schema (`page.samuelm333.Cartridges`) for `sgdb-key` persistence, permanent artwork under `~/.local/share/cartridges/covers/`, and transient preview cache under `~/.cache/cartridges/previews/`

**Testing**: Meson build and run checks (`ninja -C _build run`), blueprint compiler (`blueprint-compiler compile`), ruff (`ALL`), pyright strict type checking, and manual scenario verification

**Target Platform**: Linux Desktop (conforming to GNOME Shell and Flatpak sandbox environments)

**Project Type**: GNOME Desktop Application

**Performance Goals**: Instant credential visibility toggling (<50ms), initial centered spinner displayed in <100ms, progressive batch previews rendered smoothly without UI frame drops, cached thumbnails loaded in <300ms

**Constraints**: Strict compliance with official GNOME Human Interface Guidelines (HIG), strict Pyright static typing, Ruff ALL linting rules, isolated XDG cache directories, and a completely emoji-free codebase and documentation standard

**Scale/Scope**: Client-side UI dialog enhancements, credential presentation row, and local preview image caching

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Compliance Check | Status |
|-----------|------------------|--------|
| **I. Strict Typing & QA** | All modifications to `cover_picker.py`, `preferences.py`, and `steamgriddb.py` are strictly type-annotated, verified by `pyright` in strict mode and `ruff check`. | Pass |
| **II. Modular Game Sources** | Feature modifies UI dialogs and cache utilities; existing game source abstractions remain modular and decoupled. | Pass |
| **III. Blueprint UI** | UI changes in `cover_picker.blp` (`Gtk.Stack`, `Adw.Spinner`) and `preferences.blp` (`Adw.PasswordEntryRow`) are declared 100% in GNOME Blueprint format. | Pass |
| **IV. GNOME HIG & Portal Sandboxing** | Uses standard `Adw.PasswordEntryRow` and `Adw.Spinner` widgets conforming to GNOME HIG. No sandbox escape or direct portal bypass required. | Pass |
| **V. Resource Sandboxing & Caching** | Preview image caching strictly resides in `$XDG_CACHE_HOME/cartridges/previews/`, separate from permanent data. Network downloads execute asynchronously. Cleanup on exit and expiration prevents disk pollution. | Pass |
| **VI. Emoji-Free Standard** | Zero emoji characters are present across all specification documents, implementation plans, contracts, or source code. | Pass |

## Project Structure

### Documentation (this feature)

```text
specs/004-steamgriddb-picker/
├── spec.md              # Feature Specification
├── plan.md              # Implementation Plan (This file)
├── research.md          # Technical research & decisions (Phase 0 output)
├── data-model.md        # Data models & entity state transitions (Phase 1 output)
├── quickstart.md        # Scenario verification guide (Phase 1 output)
├── contracts/           # Interface contracts (Phase 1 output)
│   ├── cover-picker-contract.md   # Dialog stack & loading spinner contract
│   ├── image-cache-contract.md    # Preview cache & lifecycle cleanup contract
│   └── credentials-contract.md    # Password entry row contract
└── checklists/
    └── requirements.md  # Specification Quality Checklist
```

### Source Code (repository root)

```text
cartridges/
├── application.py       # [MODIFY] Hook preview cache cleanup on application shutdown
├── ui/
│   ├── cover_picker.blp # [MODIFY] Add Gtk.Stack, initial Adw.Spinner, and bottom Adw.Spinner
│   ├── cover_picker.py  # [MODIFY] Wire stack states, progressive batching, and cache lookups
│   ├── preferences.blp  # [MODIFY] Change API key row from Adw.EntryRow to Adw.PasswordEntryRow
│   └── preferences.py   # [MODIFY] Update sgdb_key_entry_row type annotation
└── utils/
    └── steamgriddb.py   # [MODIFY] Add preview cache management (get, save, prune, clear)
```

**Structure Decision**: Standard single GNOME application structure with existing modular subpackages (`cartridges/ui`, `cartridges/utils`).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
