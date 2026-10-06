# Tasks: Development Container for Build and Tooling

**Feature**: Development Container for Build and Tooling
**Branch**: `feat/007-devcontainer-build-tools`
**Spec**: [spec.md](file:///var/home/samuel/Projects/cartridges/specs/007-devcontainer-build-tools/spec.md)
**Plan**: [plan.md](file:///var/home/samuel/Projects/cartridges/specs/007-devcontainer-build-tools/plan.md)

---

## Phase 1: Setup

**Purpose**: Initialize devcontainer directory structure

- [X] T001 Create `.devcontainer` directory at repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define the base container environment, compilation toolchains, and developer user

**CRITICAL**: Foundational tasks must be completed before configuring user stories

- [X] T002 In `.devcontainer/Dockerfile`, define Fedora-based container image with compilers (`gcc`, `gcc-c++`), build engines (`meson`, `ninja-build`), and `pkg-config`
- [X] T003 In `.devcontainer/Dockerfile`, install GTK 4, Libadwaita (`gtk4-devel`, `libadwaita-devel`, `libadwaita-doc`), and `blueprint-compiler`
- [X] T004 In `.devcontainer/Dockerfile`, configure non-root user `vscode` (UID 1000) with passwordless sudo permissions

**Checkpoint**: Base container builds with native compilation toolchain and non-root developer user

---

## Phase 3: User Story 1 - One-Click Build and Test Environment (Priority: P1) - MVP

**Goal**: Enable contributors to configure, compile, and run automated test suites inside the container

**Independent Test**: Build the container image, run `meson setup _build && meson compile -C _build`, and execute `meson test -C _build -v` to verify 3/3 tests pass

### Implementation for User Story 1

- [X] T005 [P] [US1] In `.devcontainer/Dockerfile`, install Python runtime and package management tooling (`python3`, `python3-devel`, `python3-pip`, and standalone `uv` binary)
- [X] T006 [P] [US1] In `.devcontainer/devcontainer.json`, define core Dev Container specification with `name`, `build.dockerfile`, `remoteUser`, and `containerUser`
- [X] T007 [US1] Validate container image build and clean project compilation (`meson setup _build && meson compile -C _build`) per `specs/007-devcontainer-build-tools/quickstart.md`
- [X] T008 [US1] Validate automated Meson test suite execution (`meson test -C _build -v`) inside the container per `specs/007-devcontainer-build-tools/quickstart.md`

**Checkpoint**: User Story 1 functional; clean build and test suite pass out of the box in container

---

## Phase 4: User Story 2 - Automated Developer Tooling and Quality Gates (Priority: P2)

**Goal**: Pre-configure Python development dependencies, linting, formatting, and pre-commit hooks

**Independent Test**: Open the workspace in container, confirm `postCreateCommand` ran, and execute `uv run pyright` and `uv run ruff check`

### Implementation for User Story 2

- [X] T009 [P] [US2] In `.devcontainer/devcontainer.json`, configure `postCreateCommand` lifecycle hook (`uv sync --dev && uv run pre-commit install`)
- [X] T010 [P] [US2] In `.devcontainer/devcontainer.json`, configure recommended VS Code extensions (`charliermarsh.ruff`, `ms-pyright.pyright`, `ms-python.python`, `mesonbuild.mesonbuild`, `freedomevenden.blueprint-gtk`)
- [X] T011 [US2] Validate that Python quality gates (`uv run pyright` and `uv run ruff check`) run successfully inside the container environment

**Checkpoint**: User Story 2 functional; developer environment automatically configures linting, formatting, and typing

---

## Phase 5: User Story 3 - Visual Application Execution and UI Reference (Priority: P3)

**Goal**: Provide display socket passthrough for GUI preview and access to canonical reference UI tooling

**Independent Test**: Verify `/usr/bin/adwaita-1-demo` is executable and test GUI launch with display forwarding configured

### Implementation for User Story 3

- [X] T012 [P] [US3] In `.devcontainer/devcontainer.json`, add Wayland and X11 display socket mounts and environment forwarding for host GUI sessions
- [X] T013 [US3] In `.devcontainer/Dockerfile`, ensure `libadwaita-devel` provisions `/usr/bin/adwaita-1-demo` and test executable availability per Principle IV

**Checkpoint**: User Story 3 functional; UI reference demo and display forwarding available

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate configuration syntax, pre-commit compliance, and constitution rules

- [X] T014 [P] Validate `.devcontainer/devcontainer.json` syntax and schema conformance
- [X] T015 Run pre-commit quality hooks across the workspace using `uv run pre-commit run --all-files`
- [X] T016 Verify complete absence of emoji characters across all created files and documentation per Principle VI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Must run first to create directory structure
- **Foundational (Phase 2)**: Depends on Phase 1; establishes base Dockerfile and compilation tools
- **User Story 1 (Phase 3)**: Depends on Phase 2; enables complete build and test lifecycle
- **User Story 2 (Phase 4)**: Depends on Phase 3; automates Python development and pre-commit hooks
- **User Story 3 (Phase 5)**: Depends on Phase 3; adds GUI display mounts and UI demo access
- **Polish (Phase 6)**: Runs after all implementation tasks to enforce QA gates

### Parallel Opportunities

- T005 and T006 can run in parallel (Dockerfile python layer and devcontainer.json base)
- T009, T010, and T012 can run in parallel (independent sections in devcontainer.json)
- T014, T015, and T016 can execute concurrently during Phase 6

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 (Create directory)
2. Complete Phase 2 (Base Dockerfile with Meson, GCC, GTK4, Libadwaita)
3. Complete Phase 3 (Python runtime, `uv`, `devcontainer.json`, build verification)
4. Validate MVP: Project compiles cleanly and passes test suite inside the container

### Incremental Delivery
1. Foundation: Native toolchain container (Phases 1 & 2)
2. User Story 1 (MVP): One-click build and test environment (Phase 3)
3. User Story 2: Python virtualenv automation and IDE extensions (Phase 4)
4. User Story 3: GUI socket mounts and `adwaita-1-demo` reference (Phase 5)
5. Polish: Schema validation, pre-commit hooks, emoji audit (Phase 6)
