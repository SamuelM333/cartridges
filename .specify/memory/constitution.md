<!--
SYNC IMPACT REPORT:
- Version change: 2.2.0 -> 3.0.0 (includes the earlier uncommitted 2.3.0 edits)
- Bump rationale: MAJOR, because Principle VI is redefined: a blanket prohibition on emoji becomes
  "allowed as functional content, discouraged elsewhere". Existing code stays compliant, so the
  change loosens a rule rather than breaking anyone. If loosening is considered a MINOR change,
  use 2.4.0.
- List of modified principles:
  * VI. Emoji-Free Code and Documentation -> VI. Restrained Emoji Use (functional emoji allowed,
    developer-facing text discouraged, canonical check script and how to run it)
- Added principles:
  * VII. No Silent Failures and Safe Logging
- Added sections: None
- Modified sections:
  * Quality Gates & Verification: gate integrity paragraph; new item 5 (automated tests and CI);
    item 4 now covers emoji as functional content and real example output
  * Development & Branching Workflow: new bullets Commit Command, Pull Request on Implementation,
    Hook Setup, Failures Already on main, CI Logic in Scripts, AI Attribution
- Removed sections: None
- Compliance work done in the same pull request: every test script is registered as a meson
  test and CI runs the pre-commit gates and the tests (item 5); all 53 silent exception handlers
  now log or carry a `# silent-ok:` marker, enforced by `tests/test_silent_failures.py`
  (Principle VII); `check-emojis.py` covers untracked files; `CONTRIBUTING.md` documents the
  workflow rules.
- Follow-up TODOs:
  * `.claude/skills/speckit-implement/SKILL.md` does not spell out the commit, attribution, and
    pull request steps; it reads this constitution at runtime and is not modified here.
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

### VI. Restrained Emoji Use
Emoji characters are allowed as functional content: user-facing data and strings that a functional requirement in a feature's specification calls for, such as icon pickers, notifications, and similar interface content. Emoji SHOULD NOT be used anywhere else, namely in source code comments, docstrings, commit messages, specifications, architectural plans, checklists, and general markdown documentation. Functional emoji that predate this rule (for example the collection icon list) remain allowed, and third-party or tooling files (such as Spec Kit skills and templates) need not be changed.
The repository script `.specify/scripts/bash/check-emojis.py` is the canonical check. Contributors and coding agents MUST run it before every commit and before marking a feature complete. A finding in non-functional text MUST be removed or justified in the pull request description, and a finding in functional content MUST be traceable to a functional requirement in the feature's specification. With no arguments it checks unstaged changes and untracked files, and any arguments are passed to `git diff`, so `python3 .specify/scripts/bash/check-emojis.py --cached` checks staged changes. Only added lines are checked.
*Rationale*: Emoji are a legitimate part of what the application shows its users, so they are allowed there. In comments, documentation, and other developer-facing text they cause encoding discrepancies across terminal environments and visual noise in code reviews, so they are discouraged and every exception is made on purpose.

### VII. No Silent Failures and Safe Logging
Every `except` clause that discards an error MUST log it through a module-level `logging.getLogger(__name__)`. An unexpected failure (an unreadable or corrupt file, a database error, a network error) MUST be logged at WARNING or above with its traceback. An expected condition (for example a launcher that is not installed) MUST be logged at DEBUG. Routine diagnostics MUST use DEBUG so the default terminal output does not change. Log output MUST NOT contain credentials such as the SteamGridDB API key.
*Rationale*: A report of "nothing was imported" cannot be diagnosed when the failure was swallowed. Log levels keep the terminal quiet by default while the optional debug log stays detailed, and keeping credentials out of logs makes them safe to share in bug reports.

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
7. **Canonical Reference Implementation (`adwaita-1-demo`)**: The `adwaita-1-demo` application provisioned in the development environment serves as the canonical reference implementation for all Libadwaita widgets, styling patterns, and layout structures. When architecting or implementing new UI components, developers and coding agents MUST consult `adwaita-1-demo` to inspect how official patterns are constructed. UI templates and styles can be extracted directly for reference using `gresource extract /usr/bin/adwaita-1-demo <resource_path>`.

### Development Environment & Local Builds
To guarantee build environment reproducibility, all local compilation, building, and validation checks MUST be executed inside the `gtk-dev` Distrobox container. This container environment must be provisioned with the following dependencies (installed via `sudo dnf install` or equivalent): `gcc`, `meson`, `ninja-build`, `gtk4-devel`, and `libadwaita-devel` (which includes `adwaita-1-demo` for live UI reference and template extraction).

## Quality Gates & Verification
All code changes and specifications are subject to a strict automated quality gate before they can be merged or marked as complete. The file `.pre-commit-config.yaml` is the canonical source of truth for all formatting and validation steps.

**Gate integrity**: A check reported as passing MUST have inspected the changed files, including staged and untracked ones. A check that could not cover them, or could not be run in the documented environment (`gtk-dev` and `uv run`), MUST be reported as not run, never as passed.

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
   - Verification, by running `.specify/scripts/bash/check-emojis.py` as described in Principle VI, that emoji appear only as functional content.
   - Example output shown in specifications, contracts, and quickstarts MUST be copied from the implementation's real output, never written by hand.
5. **Automated Tests & CI**:
   - Every test script under `tests/` MUST be registered as a meson `test()` so `ninja -C _build test` runs it, and any build output a test needs (such as compiled GSettings schemas) MUST be produced by the build, not by hand.
   - Tests follow the existing script style: `check_*` functions called from an `if __name__ == "__main__":` runner, with the `cartridges` package stubbed as in `tests/test_hidden_games.py` when it cannot be imported.
   - The CI workflow MUST run the same gates as `.pre-commit-config.yaml` (formatters, Ruff, and Pyright) and the tests, not a subset.

## Development & Branching Workflow
To ensure stability, simplicity, and quality control during development, the following git and branching policies are strictly enforced:
* **Primary Trunk**: The `main` branch is the primary, default development trunk of the repository. It contains the active, modern codebase (formerly developed on `rewrite`).
* **Branch Source**: Any development, feature, or bugfix branches MUST be branched directly from `main`.
* **Branch Naming Convention**: Feature branches MUST follow the strict naming pattern `feat/00X-name` (e.g., `feat/003-ci-pipeline`, `feat/004-steamgriddb-picker`), where `00X` is the three-digit feature number corresponding to the feature directory in `specs/`, and `name` is a concise kebab-case descriptor. Bugfix branches must similarly follow `fix/00X-name` or `fix/short-description`.
* **Commit Command**: Every commit MUST be created with `uv run git commit` (inside the `gtk-dev` container) so the pre-commit hook runs in the project's uv environment, where Pyright and Ruff can resolve the project's dependencies and stubs. `git commit --no-verify` (or `-n`) MUST NOT be used; a failing hook MUST be fixed, not bypassed.
* **Pull Request on Implementation**: Implementing a feature (`/speckit-implement`) is not complete until its pull request is open. Once all tasks are marked done, the quality gates pass, and the work is committed with `uv run git commit` and pushed on the feature branch, the implementing agent MUST open a pull request into `main` with `gh pr create`. The pull request title MUST follow the conventional commit style of the repository history, and its body MUST summarize the change, reference `specs/00X-name/`, and state any verification that was not performed.
* **Hook Setup**: After cloning the repository or creating a new container, run `uv run pre-commit install` so the git hook points at the project's environment. A hook installed elsewhere can reference an interpreter that does not exist.
* **Failures Already on main**: A gate that fails before a change is made MUST NOT be bypassed. Fix it minimally in the same pull request and say so in the pull request description, or fix it in a separate pull request first.
* **CI Logic in Scripts**: Logic in a CI workflow beyond a single command MUST live in a script under `.github/scripts/` that can run locally. The script MUST fail with a clear error when a required tool is missing and MUST NOT silently fall back to another tool. Before merge it MUST be run in the same container image CI uses, and the pull request description MUST state what only GitHub can verify (for example the first real scheduled run).
* **AI Attribution**: Commits and pull requests produced with a coding agent MUST carry attribution. A commit message MUST end with a `Co-Authored-By:` trailer naming the agent and, when known, the model (for example `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`), and a pull request description MUST end with a line stating that it was generated with the agent and linking to the tool.
* **Short-Lived Branches Only**: All branches other than `main` must be short-lived feature or fix branches. Long-lived parallel branches are strictly prohibited.
* **Target Branch for Merges**: All merged code, pull requests, and completed feature implementations MUST be merged exclusively into the `main` branch.
* **Historical Operations**: Historical operations, legacy codebase comparisons, or inspection of pre-fork branches MUST be performed in the external repository `/var/home/samuel/Projects/cartridges-main`, keeping this repository clean.

## Governance
This Constitution governs all architectural and structural decisions. No pull request violating these core principles shall be merged.
* **Amendment Procedure**: Any modifications or additions to these principles require a dedicated pull request, explicit documentation of the rationale, and an increment of the version in accordance with the versioning policy.
* **Versioning Policy**: The version number must follow semantic versioning. Major bumps represent backward-incompatible principle removals/redefinitions. Minor bumps denote added or expanded principles. Patch bumps are reserved for minor wording clarifications and non-semantic refinements.
* **Compliance Review**: All PRs and automated workflows must verify compliance with this Constitution.

### Project Provenance & Fork Heritage
This project is an active downstream fork of the archived repository at [https://codeberg.org/kramo/cartridges](https://codeberg.org/kramo/cartridges).
* **Source Foundation**: Development builds upon the architectural foundations originally established in the upstream `rewrite` branch, which now constitutes this repository's `main` branch.
* **Code Quality Standard**: Legacy code from the original upstream repository's pre-rewrite codebase is considered of poor quality and MUST NOT be used as a design reference. Any functional components adapted from historical sources must be fully refactored to comply with Core Principle I (Strict Typing & QA).
* **New Maintenance**: This fork is actively maintained by **samuelm333** ([samuelmurillo.xyz](https://samuelmurillo.xyz)), hosted on GitHub under the username [samuelm333](https://github.com/samuelm333).

**Version**: 3.0.0 | **Ratified**: 2026-09-21 | **Last Amended**: 2026-10-11
