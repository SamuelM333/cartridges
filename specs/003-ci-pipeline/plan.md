# Implementation Plan: Automated CI Pipeline, Release Flatpak, and Nightly Builds (Linux/Flatpak)

**Branch**: `feat/003-ci-pipeline` | **Date**: 2026-09-23 | **Spec**: [specs/003-ci-pipeline/spec.md](file:///var/home/samuel/Projects/cartridges/specs/003-ci-pipeline/spec.md)

**Input**: Feature specification from `specs/003-ci-pipeline/spec.md` scoped strictly to Linux/Flatpak, with GitHub `actions/cache` commit tracking for nightly builds.

## Summary

Build and configure GitHub Actions CI/CD workflows tailored strictly to Linux and Flatpak:
1. **Pull Request & Branch CI (`ci.yml`)**: Continuous integration triggered on pull requests and pushes to `rewrite`, running code quality checks (pre-commit, Ruff, Pyright strict typechecking, Blueprint validation, Meson tests) and building the development Flatpak bundle (`page.samuelm333.Cartridges.Devel.flatpak`).
2. **Production Release Workflow (`publish-release.yml`)**: Triggered upon publishing semantic version tags (`v*`), building the production Flatpak bundle (`page.samuelm333.Cartridges.flatpak`) using `flatpak/page.samuelm333.Cartridges.json`, extracting AppStream changelog notes from `data/page.samuelm333.Cartridges.metainfo.xml.in`, and attaching the bundle to the GitHub Release.
3. **Nightly Build Workflow (`nightly.yml`)**: Triggered via daily cron schedule (`0 2 * * *`) and manual dispatch (`workflow_dispatch`), using GitHub `actions/cache` keyed on `nightly-built-${{ github.sha }}`. If the cache hits (meaning this commit has already been built), the workflow terminates immediately. If a cache miss occurs, it compiles `page.samuelm333.Cartridges.Devel.flatpak`, updates the rolling `nightly` release, and saves the commit SHA to GitHub cache.

## Technical Context

**Language/Version**: Python >= 3.13, GitHub Actions YAML, Bash, Meson >= 1.1.0, Blueprint Compiler.

**Primary Dependencies**:
- Linux Container: `bilelmoussaoui/flatpak-github-actions:gnome-47`.
- Builder Action: `flatpak/flatpak-github-actions/flatpak-builder@v6.5`.
- Workflow Utilities: `actions/checkout@v4`, `actions/cache@v4`, `softprops/action-gh-release@v2.2.2`.

**Storage**: GitHub Actions cache storage (`actions/cache@v4`) for commit SHA deduplication; GitHub Releases for artifact hosting.

**Testing**: Meson unit tests (`ninja -C _build test`), Pyright strict mode, Ruff lint/format, desktop/appstream/schema validation.

**Target Platform**: Linux (Flatpak x86_64).

**Project Type**: Desktop application / CI-CD pipeline infrastructure.

**Performance Goals**: PR checks execute under 10 minutes; nightly deduplication check evaluates and terminates within 30 seconds on duplicate commits.

**Constraints**:
- Strict adherence to Constitution Principle I (Quality Assurance), Principle IV (Sandboxing & Libadwaita), and Principle VI (Zero Unicode Emojis).
- Production release manifests and configurations must use updated application ID `page.samuelm333.Cartridges`.
- Zero dependencies on Windows (Inno Setup) or macOS (PyInstaller).

**Scale/Scope**: 3 GitHub Actions workflow files (`ci.yml`, `publish-release.yml`, `nightly.yml`) and 1 production Flatpak manifest (`flatpak/page.samuelm333.Cartridges.json`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I (Strict Typing & QA)**: All scripts inside workflows are statically typed and checked with Pyright and Ruff.
- [x] **Principle IV (Libadwaita & Desktop Integration)**: Official AppStream metadata and desktop file integration are preserved and validated.
- [x] **Principle V (Resource & Asset Sandboxing)**: Flatpak manifests retain isolated XDG paths and portal permissions.
- [x] **Principle VI (Zero Unicode Emojis)**: Zero emoji characters across all workflow YAML files, scripts, or markdown artifacts. Verified with `check-emojis.py`.
- [x] **Principle VII (Branching Workflow)**: CI triggers on pull requests and pushes to `rewrite`. Feature branch `feat/003-ci-pipeline` branched from `rewrite`.

## Project Structure

### Documentation (this feature)

```text
specs/003-ci-pipeline/
├── plan.md              # Implementation Plan
├── research.md          # Technical research & design choices
├── data-model.md        # Entities & cache state models
├── quickstart.md        # Validation walkthrough
├── contracts/           # Workflow triggers & interfaces
│   ├── ci-workflow.md
│   ├── release-workflow.md
│   └── nightly-workflow.md
├── checklists/
│   └── requirements.md
└── tasks.md             # (Generated in tasks phase)
```

### Source Code (repository root)

```text
.github/
└── workflows/
    ├── ci.yml                 # Pull request and branch CI (Linux Flatpak & Quality checks)
    ├── nightly.yml            # Deduplicated nightly Flatpak build
    └── publish-release.yml    # Tag-triggered production Flatpak release

flatpak/
├── page.samuelm333.Cartridges.Devel.json  # Existing devel manifest
├── page.samuelm333.Cartridges.json        # Production release manifest
├── python3-pillow.json
└── python3-pybind11.json
```
