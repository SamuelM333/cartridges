# Tasks: Automated CI Pipeline, Release Flatpak, and Nightly Builds (Linux/Flatpak)

**Input**: Design artifacts from `specs/003-ci-pipeline/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`).

## Phase 1: Setup & Shared Infrastructure

**Purpose**: Workflow and Flatpak configuration initialization

- [x] T001 [P] Create GitHub workflows directory structure `.github/workflows/`
- [x] T002 [P] Create production Flatpak manifest in `flatpak/page.samuelm333.Cartridges.json` configured with `-Dprofile=release`, stable runtime `org.gnome.Platform//47` and SDK `org.gnome.Sdk//47`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared utilities for release changelog extraction and manifest validation

- [x] T003 Create release notes extraction script in `.github/scripts/extract_release_notes.py` parsing AppStream `<release>` tags from `data/page.samuelm333.Cartridges.metainfo.xml.in`
- [x] T004 Validate manifest JSON integrity and verify both `flatpak/page.samuelm333.Cartridges.json` and `flatpak/page.samuelm333.Cartridges.Devel.json` match required module architectures

**Checkpoint**: Shared infrastructure ready - workflow implementation can proceed

---

## Phase 3: User Story 1 - Automated Production Flatpak Release Distribution (Priority: P1) 🎯 MVP

**Goal**: Automatically build and attach `page.samuelm333.Cartridges.flatpak` to GitHub Releases on `v*` tag push

**Independent Test**: Simulate or inspect the release workflow structure: verify tag filter `v*`, permissions `contents: write`, `flatpak-builder` invocation with production manifest, and `softprops/action-gh-release` asset upload.

### Implementation for User Story 1

- [x] T005 [US1] Create production release workflow in `.github/workflows/publish-release.yml` triggered on push tags `v*` with `contents: write` permissions
- [x] T006 [US1] Configure Flatpak builder step in `.github/workflows/publish-release.yml` using `bilelmoussaoui/flatpak-github-actions:gnome-47` and `flatpak/flatpak-github-actions/flatpak-builder@v6.5` with bundle name `page.samuelm333.Cartridges.flatpak`
- [x] T007 [US1] Wire release note extraction and GitHub Release publication step in `.github/workflows/publish-release.yml` using `softprops/action-gh-release@v2.2.2` attaching `page.samuelm333.Cartridges.flatpak`

**Checkpoint**: User Story 1 workflow complete and testable independently

---

## Phase 4: User Story 2 - Nightly Flatpak Builds with actions/cache Deduplication (Priority: P2)

**Goal**: Build `page.samuelm333.Cartridges.Devel.flatpak` on schedule/dispatch, skipping build when commit SHA matches `actions/cache`

**Independent Test**: Verify `.github/workflows/nightly.yml` evaluates cache key `nightly-built-${{ github.sha }}`; on cache hit skips build; on miss builds development Flatpak, updates `nightly` release, and saves cache.

### Implementation for User Story 2

- [x] T008 [US2] Create nightly build workflow in `.github/workflows/nightly.yml` with schedule cron `0 2 * * *` and `workflow_dispatch` trigger
- [x] T009 [US2] Implement cache check step in `.github/workflows/nightly.yml` using `actions/cache@v4` with key `nightly-built-${{ github.sha }}` and path `.nightly-flag`
- [x] T010 [US2] Implement conditional Flatpak build step in `.github/workflows/nightly.yml` running on `steps.check-cache.outputs.cache-hit != 'true'` to build `page.samuelm333.Cartridges.Devel.flatpak`
- [x] T011 [US2] Implement release update and cache save steps in `.github/workflows/nightly.yml` updating the `nightly` release with bundle and saving `.nightly-flag` to cache

**Checkpoint**: User Story 2 workflow complete and testable independently

---

## Phase 5: User Story 3 - Pull Request & Push Quality & Flatpak CI (Priority: P3)

**Goal**: Validate pre-commit hooks, Pyright strict typing, Meson test suite, and Flatpak build on PRs and pushes to `rewrite`

**Independent Test**: Verify `.github/workflows/ci.yml` triggers on push/PR to `rewrite`, executes pre-commit hygiene, and builds devel Flatpak.

### Implementation for User Story 3

- [x] T012 [US3] Create CI workflow in `.github/workflows/ci.yml` triggered on push to `rewrite` and pull requests targeting `rewrite` with concurrency group
- [x] T013 [US3] Add code quality & validation job (`lint-and-test`) in `.github/workflows/ci.yml` running pre-commit checks, Pyright strict typing, blueprint compiler check, and meson unit tests
- [x] T014 [US3] Add development Flatpak build job (`flatpak`) in `.github/workflows/ci.yml` compiling `flatpak/page.samuelm333.Cartridges.Devel.json`

**Checkpoint**: User Story 3 CI workflow complete and testable independently

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validation, hygiene, and documentation

- [x] T015 Run pre-commit hooks (`uv run pre-commit run --all-files`) and verify formatting of all YAML, JSON, and Python files
- [x] T016 Run emoji check script (`python3 .specify/scripts/bash/check-emojis.py`) and verify 0 emojis across all files
- [x] T017 Execute validation scenarios from `specs/003-ci-pipeline/quickstart.md`

---

## Phase 7: Convergence

**Purpose**: Remediate CI execution failures surfaced in `ci-logs/logs_97164028902`

- [x] T018 Fix Flatpak runtime version in `flatpak/page.samuelm333.Cartridges.Devel.json` by updating `"runtime-version"` from `"master"` to `"47"` per FR-003, US3/AC1 (contradicts)
- [x] T019 Add `blueprint-compiler` to package installation step in `.github/workflows/ci.yml` per FR-002, US3/AC1 (missing)

---

## Phase 8: Convergence

**Purpose**: Remediate CI execution failures surfaced in `ci-logs/logs_97168997700`

- [x] T020 Add `blueprint-compiler` build module to `flatpak/page.samuelm333.Cartridges.Devel.json` and `flatpak/page.samuelm333.Cartridges.json` per FR-001, FR-003, US1/AC1, US2/AC1 (missing)
- [x] T021 Add `gettext` to `dnf install` packages in `.github/workflows/ci.yml` to provide `msgfmt` per FR-002, US3/AC1 (missing)

---

## Phase 9: GNOME Runtime 50 Update

**Purpose**: Update Flatpak manifests and CI workflow containers to GNOME Runtime 50

- [x] T022 Update `"runtime-version"` to `"50"` in `flatpak/page.samuelm333.Cartridges.Devel.json` and `flatpak/page.samuelm333.Cartridges.json`
- [x] T023 Update container image to `ghcr.io/flathub-infra/flatpak-github-actions:gnome-50` in `.github/workflows/ci.yml`, `.github/workflows/publish-release.yml`, and `.github/workflows/nightly.yml`
