<!--
SYNC IMPACT REPORT:
- Version change: 1.5.0 -> 1.6.0
- List of modified principles:
  * Principle I: "Strict Typing & Quality Assurance" -> "Strict Typing, Code Formatting & Quality Assurance" (mandates running repository formatting tools prior to marking any feature or spec complete)
- Added sections: None
- Modified sections:
  * Quality Gates & Verification: explicitly establishes `.pre-commit-config.yaml` as the canonical source of truth for mandatory formatting steps that must run before completing any spec or merging changes.
- Removed sections: None
- Follow-up TODOs: None
-->

# Cartridges Constitution

## Core Principles

### I. Strict Typing, Code Formatting & Quality Assurance
The project runs Pyright in `strict` type-checking mode and Ruff with the complete rule set (`ALL`). Every new Python module, function, and class MUST have complete, correct type annotations. No typed variables or parameters can be left untyped, and `Any` must be avoided unless strictly necessary and accompanied by a detailed justification comment. All code formatting and linting tools defined in `.pre-commit-config.yaml` MUST be executed and pass before any feature or specification is marked as complete. All code must pass Ruff formatting and linting without errors before merge.
*Rationale*: Using Python in a large desktop application context can lead to runtime fragility. Strict static typing, uniform automated code formatting, and aggressive linting ensure that regressions, stylistic drift, and syntax inconsistencies are resolved at development time rather than on user machines.

### II. Modular Game Sources
Every supported game launcher or distribution channel (e.g., Steam, Lutris, Heroic) must be implemented as an independent, self-contained subclass under the `cartridges/sources/` package. Game sources must expose a unified interface, must be independently queryable, and must never contain hard-coded GUI dependencies. They must focus solely on parsing, discovery, and retrieving metadata/covers.
*Rationale*: Decoupling game extraction logic from presentation logic ensures that sources can be tested independently, and makes adding new launchers highly modular.

### III. Blueprint-Driven Declarative UI
All user interface templates must be designed declaratively using GNOME Blueprint (`.blp`) files rather than raw XML or procedural Python UI construction. Code-behind controller classes (subclasses of `Gtk.Widget` or custom GObjects) must cleanly map to these templates using `Gtk.Template` helpers. UI layout and application logic must remain strictly decoupled.
*Rationale*: Blueprint files provide a concise, readable syntax for GTK UI layouts that reduces boilerplate and improves maintainability compared to traditional UI definition XMLs or procedural Python layout code.

### IV. Libadwaita Patterns, GNOME HIG & Desktop Integration
Cartridges is designed primarily as a first-class GNOME citizen. The application interface MUST strictly follow the official GNOME Human Interface Guidelines (https://developer.gnome.org/hig/) and implement Libadwaita design patterns and practices standard for modern GNOME applications. Custom controls and non-standard layouts are forbidden when an established Libadwaita pattern exists. The application must behave seamlessly inside sandbox environments like Flatpak. Any file operations, subprocess executions, or external launcher calls must respect sandboxing boundaries and provide fallback paths or clear error messages when permissions are constrained.
*Rationale*: Strict adherence to the GNOME Human Interface Guidelines and standard Libadwaita patterns guarantees that Cartridges feels native, intuitive, accessible, responsive across adaptive form factors, and visually coherent with the GNOME ecosystem.

### V. Resource and Asset Sandboxing
Game covers, icons, and configuration data must be managed through clean, isolated data directory pathways conforming to the standard XDG directory layout. CSS stylesheets and Blueprint-derived UI definitions must be bundled cleanly via GResource. External resource fetching (e.g. steam cover downloads) must be handled asynchronously to avoid blocking the GTK main thread, and must support offline caching.
*Rationale*: Proper caching and resource scoping prevent disk pollution, keep the application fully responsive under poor network conditions, and ensure security.

### VI. Emoji-Free Code and Documentation
Emoji characters MUST NOT be used anywhere in the codebase or project documentation. This prohibition applies to source code, comments, docstrings, Blueprint templates, commit messages, specifications, architectural plans, checklists, and general markdown documentation.
*Rationale*: Enforcing an emoji-free standard prevents character encoding discrepancies across varied terminal environments and tools, avoids visual noise in code reviews, and preserves a clean, professional technical presentation.

## Technical Constraints & Sandbox Compliance
As a Flatpak-first application, Cartridges must adhere to strict desktop isolation constraints. Direct execution of files outside the sandbox must be negotiated via appropriate portal integrations (such as the Flatpak portal or host command execution portals) whenever sandbox permissions restrict direct execution. Dependency on host commands should be handled gracefully with diagnostic errors instead of crashing the UI.

### Libadwaita Patterns & GNOME HIG Conventions
All UI components in Cartridges MUST adopt standard Libadwaita patterns and common GNOME application practices:
1. **Window and Structure**: Use `Adw.ApplicationWindow`, `Adw.ToolbarView`, `Adw.HeaderBar`, and `Adw.ToastOverlay` for top-level window architecture.
2. **Preferences & Settings**: Implement configuration dialogs using `Adw.PreferencesDialog`, organized into `Adw.PreferencesPage` and `Adw.PreferencesGroup` sections with standard rows (`Adw.ActionRow`, `Adw.SwitchRow`, `Adw.EntryRow`, `Adw.ExpanderRow`, `Adw.ComboRow`).
3. **Dialogs & Alerts**: Use `Adw.AlertDialog` for modal alerts, destructive action confirmations, and critical user prompts. Avoid deprecated or raw `Gtk.MessageDialog`/`Gtk.Dialog`.
4. **Adaptive Presentation & Layout**: Utilize `Adw.Breakpoint` to ensure responsive adaptation between desktop and compact mobile/handheld dimensions. Keep layout margins, paddings, and typography standard with Libadwaita system tokens.
5. **Feedback & Progress**: Use in-app `Adw.Toast` notifications (with undo actions for destructive operations) rather than intrusive blocking dialogs for non-critical confirmations. Display progress using standard `Gtk.ProgressBar` or `Adw.Spinner` embedded directly in contextual action rows.
6. **Actions & Menus**: Leverage `Gio.ActionGroup`, `Gio.ActionMap`, and `Gtk.MenuButton` with standard GNOME primary menu structures and keyboard shortcuts.

### Development Environment & Local Builds
To guarantee build environment reproducibility, all local compilation, building, and validation checks MUST be executed inside the `gtk-dev` Distrobox container. This container environment must be provisioned with the following dependencies (installed via `sudo dnf install` or equivalent): `gcc`, `meson`, `ninja-build`, and `gtk4-devel`.

## Quality Gates & Verification
All code changes and specifications are subject to a strict automated quality gate before they can be merged or marked as complete. The file `.pre-commit-config.yaml` is the canonical source of truth for all formatting and validation steps.

Before marking any specification or feature as complete, the following checks MUST be executed and pass:
1. **Code Formatting & Cleanliness**: Run all formatters configured in `.pre-commit-config.yaml` (or `pre-commit run --all-files`):
   - Pre-commit hygiene: trailing whitespace, end-of-file fixer, large file checks, and file content sorting (`po/LINGUAS`, `po/POTFILES.in`).
   - Python formatting and import sorting: `ruff check --select I --fix` and `ruff format`.
   - Blueprint layout formatting: `blueprint-compiler format --fix --no-diff` on all `.blp` files.
   - Meson build configuration formatting: `meson format --inplace` on all `meson.build` and `meson.options` files.
   - Prettier formatting: `prettier --write` on all CSS, JSON, and YAML files.
   - SVG vector optimization: `svgo` on SVG assets.
2. **Static Analysis & Linting**:
   - Pyright static analysis in `strict` mode (`pyright`).
   - Ruff lint verification (`ruff check`).
3. **Build & Template Compilation**:
   - Verification that all Blueprint templates compile without errors via `blueprint-compiler`.
   - Meson configuration and build checks (`meson setup _build` and `ninja -C _build test`).
   - Validation of desktop files, AppStream metadata, and GSettings schemas.
4. **Documentation & Formatting Integrity**:
   - Verification that all code, docstrings, and documentation remain completely free of emoji characters.

## Development & Branching Workflow
To ensure stability and quality control during development, the following git and branching policies are strictly enforced:
* **Branch Source**: Any development, feature, or bugfix branches MUST be branched directly from the `rewrite` branch. Feature branches must not be branched from `main`.
* **Branch Protection for main**: The `main` branch is kept completely frozen. No direct pushes or merges to `main` are allowed.
* **Target Branch for Merges**: All merged code, pull requests, and completed feature implementations MUST be merged exclusively into the `rewrite` branch.

## Governance
This Constitution governs all architectural and structural decisions. No pull request violating these core principles shall be merged.
* **Amendment Procedure**: Any modifications or additions to these principles require a dedicated pull request, explicit documentation of the rationale, and an increment of the version in accordance with the versioning policy.
* **Versioning Policy**: The version number must follow semantic versioning. Major bumps represent backward-incompatible principle removals/redefinitions. Minor bumps denote added or expanded principles. Patch bumps are reserved for minor wording clarifications and non-semantic refinements.
* **Compliance Review**: All PRs and automated workflows must verify compliance with this Constitution.

### Project Provenance & Fork Heritage
This project is an active downstream fork of the archived repository at [https://codeberg.org/kramo/cartridges](https://codeberg.org/kramo/cartridges).
* **Source Foundation**: Development MUST build upon and align with the legacy codebase's `rewrite` branch, which contains the most up-to-date and high-quality architectural foundations.
* **Code Quality Standard**: Legacy code from the original `main` branch of the upstream repository is considered of poor quality and MUST NOT be used as a design reference. Any functional legacy components brought over or adapted from that branch must be fully refactored to comply with Core Principle I (Strict Typing & QA).
* **New Maintenance**: This fork is actively maintained by **samuelm333** ([samuelmurillo.xyz](https://samuelmurillo.xyz)), hosted on GitHub under the username [samuelm333](https://github.com/samuelm333).

**Version**: 1.6.0 | **Ratified**: 2026-09-21 | **Last Amended**: 2026-09-23
