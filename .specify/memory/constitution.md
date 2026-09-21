<!--
SYNC IMPACT REPORT:
- Version change: 1.4.0 -> 1.4.1
- List of modified principles: None
- Added sections:
  * Development Environment & Local Builds (under Technical Constraints & Sandbox Compliance)
- Removed sections: None
- Follow-up TODOs: None
-->

# Cartridges Constitution

## Core Principles

### I. Strict Typing & Quality Assurance
The project runs Pyright in `strict` type-checking mode and Ruff with the complete rule set (`ALL`). Every new Python module, function, and class MUST have complete, correct type annotations. No typed variables or parameters can be left untyped, and `Any` must be avoided unless strictly necessary and accompanied by a detailed justification comment. All code must pass Ruff formatting and linting without errors before merge.
*Rationale*: Using Python in a large desktop application context can lead to runtime fragility. Strict static typing and aggressive linting ensure that regressions are caught at development time rather than on user machines.

### II. Modular Game Sources
Every supported game launcher or distribution channel (e.g., Steam, Lutris, Heroic) must be implemented as an independent, self-contained subclass under the `cartridges/sources/` package. Game sources must expose a unified interface, must be independently queryable, and must never contain hard-coded GUI dependencies. They must focus solely on parsing, discovery, and retrieving metadata/covers.
*Rationale*: Decoupling game extraction logic from presentation logic ensures that sources can be tested independently, and makes adding new launchers highly modular.

### III. Blueprint-Driven Declarative UI
All user interface templates must be designed declaratively using GNOME Blueprint (`.blp`) files rather than raw XML or procedural Python UI construction. Code-behind controller classes (subclasses of `Gtk.Widget` or custom GObjects) must cleanly map to these templates using `Gtk.Template` helpers. UI layout and application logic must remain strictly decoupled.
*Rationale*: Blueprint files provide a concise, readable syntax for GTK UI layouts that reduces boilerplate and improves maintainability compared to traditional UI definition XMLs or procedural Python layout code.

### IV. GNOME Human Interface Guidelines (HIG) & Desktop Integration
Cartridges is designed primarily as a first-class GNOME citizen. The application interface MUST strictly follow the official GNOME Human Interface Guidelines (https://developer.gnome.org/hig/) and leverage Libadwaita design patterns for layouts, navigation, and controls. The application must behave seamlessly inside sandbox environments like Flatpak. Any file operations, subprocess executions, or external launcher calls must respect sandboxing boundaries and provide fallback paths or clear error messages when permissions are constrained.
*Rationale*: Strict adherence to the GNOME Human Interface Guidelines guarantees that Cartridges feels native, intuitive, accessible, and coherent with the wider GNOME desktop environment, while sandbox compliance ensures robust Flatpak distribution.

### V. Resource and Asset Sandboxing
Game covers, icons, and configuration data must be managed through clean, isolated data directory pathways conforming to the standard XDG directory layout. CSS stylesheets and Blueprint-derived UI definitions must be bundled cleanly via GResource. External resource fetching (e.g. steam cover downloads) must be handled asynchronously to avoid blocking the GTK main thread, and must support offline caching.
*Rationale*: Proper caching and resource scoping prevent disk pollution, keep the application fully responsive under poor network conditions, and ensure security.

### VI. Emoji-Free Code and Documentation
Emoji characters MUST NOT be used anywhere in the codebase or project documentation. This prohibition applies to source code, comments, docstrings, Blueprint templates, commit messages, specifications, architectural plans, checklists, and general markdown documentation.
*Rationale*: Enforcing an emoji-free standard prevents character encoding discrepancies across varied terminal environments and tools, avoids visual noise in code reviews, and preserves a clean, professional technical presentation.

## Technical Constraints & Sandbox Compliance
As a Flatpak-first application, Cartridges must adhere to strict desktop isolation constraints. Direct execution of files outside the sandbox must be negotiated via appropriate portal integrations (such as the Flatpak portal or host command execution portals) whenever sandbox permissions restrict direct execution. Dependency on host commands should be handled gracefully with diagnostic errors instead of crashing the UI.

### Development Environment & Local Builds
To guarantee build environment reproducibility, all local compilation, building, and validation checks MUST be executed inside the `gtk-dev` Distrobox container. This container environment must be provisioned with the following dependencies (installed via `sudo dnf install` or equivalent): `gcc`, `meson`, `ninja-build`, and `gtk4-devel`.

## Quality Gates & Verification
All code changes are subject to a strict automated quality gate before they can be merged. This includes:
1. Complete static analysis check with Pyright in `strict` mode (`pyright`).
2. Code style, linting, and sorting with Ruff (`ruff check` and `ruff format`).
3. Verification that all Blueprint templates compile successfully via the Blueprint Compiler and adhere to GNOME HIG design patterns.
4. Validation of translation catalogs (PO files) and meson configuration builds (`meson setup _build`).
5. Verification that code and documentation remain free of emoji characters.

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

**Version**: 1.4.1 | **Ratified**: 2026-09-21 | **Last Amended**: 2026-09-21
