# Feature Specification: Automated CI Pipeline, Release Flatpak, and Nightly Builds (Linux/Flatpak)

**Feature Branch**: `feat/003-ci-pipeline`

**Created**: 2026-09-23

**Status**: Draft

**Input**: User description: "003 Bring back the CI pipeline available in main. Requirements: Build flatpak on release. Build nightly flatpak - Avoid building and releasing the same commit multiple times. Scope decisions: reduce the scope to just linux/flatpak. Keep using GitHub Actions. Use GitHub actions/cache to keep the last built git hash and use that as flag."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automated Production Flatpak Release Distribution (Priority: P1)

As a Cartridges maintainer and end user on Linux, I want GitHub Actions to automatically build and attach the official release-ready Flatpak bundle whenever a release tag is published, so that release packages are reliably compiled against the stable GNOME runtime, signed/bundled, and downloadable directly from GitHub Releases without manual build intervention.

**Why this priority**: Official Flatpak distribution on GitHub Releases provides verified, reproducible application bundles immediately upon release, enabling users on immutable or offline Linux distributions to install official releases.

**Independent Test**: Trigger a release workflow on a version tag (e.g. `v2.0.0`). Verify that GitHub Actions builds the production Flatpak bundle `page.samuelm333.Cartridges.flatpak` using the release manifest, extracts release notes from AppStream metadata, and attaches the bundle to the GitHub Release.

**Acceptance Scenarios**:

1. **Given** a new version tag (e.g. `v2.0.0`) pushed to the repository, **When** the release pipeline executes, **Then** it builds the production Flatpak bundle `page.samuelm333.Cartridges.flatpak` via `flatpak-builder` using `flatpak/page.samuelm333.Cartridges.json`.
2. **Given** a successful release Flatpak build, **When** the release job completes, **Then** the `.flatpak` bundle is attached to the GitHub Release alongside release notes parsed from `data/page.samuelm333.Cartridges.metainfo.xml.in`.
3. **Given** a compilation failure during the Flatpak build, **When** that job fails, **Then** the pipeline halts and reports failure before publishing incomplete release artifacts.

---

### User Story 2 - Nightly Flatpak Builds with actions/cache Commit Tracking (Priority: P2)

As a tester and early-adopter user, I want nightly Flatpak builds generated from the `rewrite` branch on a regular schedule (or workflow dispatch), while automatically skipping redundant builds if no new commits have landed since the last nightly run using `actions/cache`, so that GitHub Actions compute resources are conserved and users do not download duplicate packages.

**Why this priority**: Continuous testing on development builds allows catching regressions early on the latest GNOME development runtimes while eliminating unnecessary CI churn and redundant releases. Using GitHub `actions/cache` to store the last-built git SHA provides an instant, self-contained mechanism without requiring extra repository commits or API calls.

**Independent Test**: Run the nightly workflow on a new commit on `rewrite`. Confirm that the cache does not match the current commit SHA, the nightly Flatpak bundle is built and published to the `nightly` release, and the current commit SHA is saved into `actions/cache`. Then trigger the workflow again on the same commit and confirm that the cache hit detects the identical commit SHA and skips building and publishing.

**Acceptance Scenarios**:

1. **Given** a scheduled or manually dispatched nightly workflow run, **When** `actions/cache` is queried with the key based on the current HEAD commit SHA, **Then** if the cache key is not found (cache miss), the workflow proceeds to build `page.samuelm333.Cartridges.Devel.flatpak`.
2. **Given** a successful nightly build, **When** the publish step finishes, **Then** the new bundle is uploaded to the Nightly release and the current commit SHA is saved to GitHub cache.
3. **Given** the nightly workflow runs when HEAD on `rewrite` matches the commit SHA stored in `actions/cache` (cache hit), **When** the check step evaluates the cache status, **Then** all compilation and publishing jobs are cleanly skipped.

---

### User Story 3 - Pull Request & Push Code Quality & Flatpak CI (Priority: P3)

As a contributor and reviewer, I want automated CI validation to run on every pull request and push to `rewrite`, validating code formatting, typing, blueprint compilation, test suites, and verifying that the development Flatpak compiles cleanly, so that broken commits and regressions are caught before merging.

**Why this priority**: Enforces Constitution Principle I (Strict Typing & QA) automatically on all incoming changes before maintainers review and merge code.

**Independent Test**: Push a commit or create a PR targeting `rewrite`. Verify that automated checks execute pre-commit hooks, Pyright, Meson tests, and development Flatpak build validation.

**Acceptance Scenarios**:

1. **Given** a pull request targeting `rewrite`, **When** the CI workflow triggers, **Then** it verifies pre-commit formatting, static typing, and builds the development Flatpak bundle `page.samuelm333.Cartridges.Devel.flatpak` to ensure no compilation regressions.
2. **Given** a commit that introduces formatting discrepancies, type errors, or broken blueprint files, **When** CI runs, **Then** the workflow fails with detailed diagnostic step logs.

---

### Edge Cases

- **Cache miss on first run**: When no cache entry exists yet, the nightly workflow must treat this as a cache miss and proceed with building and storing the SHA in the cache.
- **Concurrent runs on rapid pushes**: What happens if multiple commits or tags are pushed in quick succession? Workflow concurrency groups must cancel in-progress runs for pull requests and development pushes, while ensuring tag/release jobs complete sequentially without artifact collisions.
- **Missing or invalid release metadata**: How does the release workflow handle missing `<release>` tags in `page.samuelm333.Cartridges.metainfo.xml.in`? It must fail gracefully or fall back to git tag annotations rather than crashing or publishing blank release notes.
- **Workflow token permissions**: Release creation and tag updates require explicit repository write permissions (`contents: write`). Workflows must explicitly declare minimal required permissions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a continuous integration workflow (`ci.yml`) triggered on pull requests and pushes to `rewrite`.
- **FR-002**: The CI workflow MUST run code quality checks including pre-commit hooks, Pyright strict type analysis, and Meson unit tests.
- **FR-003**: The CI workflow MUST build the development Flatpak bundle `page.samuelm333.Cartridges.Devel.flatpak` on Linux to verify build reproducibility.
- **FR-004**: The system MUST provide a release workflow triggered when a semantic version tag (e.g. `v*`) is pushed.
- **FR-005**: The release workflow MUST build the production Flatpak bundle `page.samuelm333.Cartridges.flatpak` using the official application ID `page.samuelm333.Cartridges` and the production manifest `flatpak/page.samuelm333.Cartridges.json`.
- **FR-006**: The release workflow MUST extract release notes for the published version from `data/page.samuelm333.Cartridges.metainfo.xml.in`.
- **FR-007**: The release workflow MUST attach the built Linux Flatpak bundle to the GitHub Release matching the pushed tag.
- **FR-008**: The system MUST provide a nightly build workflow (`nightly.yml`) triggered via schedule (e.g., daily cron) and manual dispatch (`workflow_dispatch`).
- **FR-009**: The nightly workflow MUST use `actions/cache` to store and restore the commit SHA of the last successfully built nightly package.
- **FR-010**: The nightly workflow MUST skip the Flatpak build and release publication when the cached commit SHA matches the current HEAD commit SHA of the target branch.
- **FR-011**: The nightly workflow MUST build `page.samuelm333.Cartridges.Devel.flatpak` on a cache miss (new commit) and update the designated `nightly` release with the new bundle and update the cache.
- **FR-012**: All workflows MUST declare strict minimal `permissions` adhering to the principle of least privilege.
- **FR-013**: All workflow definitions and accompanying scripts MUST contain zero Unicode emoji characters.

### Key Entities

- **Release Artifact**: Represents an official release distribution package (`page.samuelm333.Cartridges.flatpak`), tied to an immutable git tag and published on GitHub Releases with validated AppStream changelog notes.
- **Nightly Artifact**: Represents a rolling pre-release package (`page.samuelm333.Cartridges.Devel.flatpak`) built from the latest commit on `rewrite`, updated only when code changes are detected.
- **Cache Key**: A cache identifier maintained via `actions/cache` storing the git commit SHA of the most recent successful nightly build.
- **Flatpak Manifest**: JSON specification defining the runtime, SDK, sandboxed permissions, and compilation commands for either development (`Devel`) or production releases.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every git tag push triggers automated compilation of the Linux Flatpak bundle and attaches it to the GitHub Release without manual maintainer intervention.
- **SC-002**: Scheduled nightly workflows evaluate `actions/cache` and completely skip build tasks in 100% of runs where HEAD has not advanced past the last cached nightly build commit SHA.
- **SC-003**: Pull request builds detect and reject formatting errors, type discrepancies, and build failures within 10 minutes of push.
- **SC-004**: Zero Unicode emojis are present across any created workflow configuration files or automated scripts.

## Assumptions

- Scope is strictly Linux and Flatpak; Windows and macOS builds from legacy `cartridges-main` are intentionally excluded.
- Development occurs primarily on the `rewrite` branch as mandated by Constitution Core Principle VII.
- GitHub Actions is the CI/CD execution platform for the repository.
- GitHub token credentials supplied by `GITHUB_TOKEN` have permission to publish releases when configured with `contents: write`.
- The production Flatpak manifest `flatpak/page.samuelm333.Cartridges.json` will be maintained in the repository alongside `flatpak/page.samuelm333.Cartridges.Devel.json`.
