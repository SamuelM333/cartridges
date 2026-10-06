# Feature Specification: Development Container for Build and Tooling

**Feature Branch**: `feat/007-devcontainer-build-tools`

**Created**: 2026-10-07
**Updated**: 2026-10-07

**Status**: Complete

**Input**: User description: "new feat: define a devcontainer with the tools needed to build the app like meson"

## User Scenarios & Testing

### User Story 1 - One-Click Build and Test Environment (Priority: P1)

Contributors and developers opening the Cartridges repository need an isolated, reproducible development container with all native compilation tools (Meson, Ninja, C compiler, system headers) pre-installed, so they can configure, build, and test Cartridges immediately without installing developer packages onto their host system.

**Why this priority**: Core developer onboarding and environment reproducibility. Setting up GTK 4, Libadwaita, and Meson build environments manually across varied host operating systems is error-prone. A self-contained devcontainer eliminates setup friction and guarantees consistent build behavior.

**Independent Test**: Open the repository in a container engine using the devcontainer definition, configure the Meson build directory, compile the application, and run the automated test suite. The build and tests must succeed without any prior host-level software installation.

**Acceptance Scenarios**:

1. **Given** a developer environment with a supported container runtime, **When** the developer starts the devcontainer, **Then** the container environment initializes with all required compilers, build system tools (Meson, Ninja), and toolkit libraries available in the system path.
2. **Given** the active devcontainer environment, **When** the developer executes the standard build configuration and compile sequence, **Then** the Cartridges build completes successfully without missing header or library errors.
3. **Given** the active devcontainer environment, **When** the developer runs the test suite, **Then** all schema validation, desktop file validation, appstream validation, and Python test suites pass cleanly.

---

### User Story 2 - Automated Developer Tooling and Quality Gates (Priority: P2)

Contributors writing code or preparing pull requests need Python tooling, linters, formatters, and type checkers pre-configured inside the container, so they can validate their code against repository standards before committing.

**Why this priority**: Consistent code quality and adherence to repository constitution principles (strict typing, Ruff formatting, pre-commit validation) without requiring developers to troubleshoot local Python virtual environments.

**Independent Test**: Inside the devcontainer, run pre-commit quality checks, type checking, and code formatting commands. All checks should execute and report status without missing tool dependencies.

**Acceptance Scenarios**:

1. **Given** the devcontainer environment, **When** the container completes initial setup, **Then** the Python development dependencies (including `uv`, Pyright, Ruff, and pre-commit) are installed and ready for execution.
2. **Given** modified files in the workspace, **When** running the pre-commit checks or individual linters inside the container, **Then** all checks execute smoothly without environment or PATH resolution errors.

---

### User Story 3 - Visual Application Execution and UI Reference (Priority: P3)

Developers designing or modifying user interface components need the container to support graphical execution and access to reference UI tooling, so they can preview the application and inspect standard Libadwaita patterns.

**Why this priority**: Enhances the developer feedback loop when modifying Blueprint UI files or testing visual widgets, and supports the project constitution requirement to consult reference implementations.

**Independent Test**: On a host system configured for display forwarding, run the application or reference demo tool from inside the container and verify that an interactive window appears.

**Acceptance Scenarios**:

1. **Given** a host environment supporting display socket forwarding (Wayland or X11), **When** Cartridges is executed from inside the container, **Then** the graphical window opens and interacts with the desktop session.
2. **Given** the container environment, **When** the developer runs or inspects reference UI tooling (such as `adwaita-1-demo`), **Then** the tool is accessible and its templates can be extracted or examined.

---

### Edge Cases

- **Headless Host Environments**: When the devcontainer is started in a headless environment (such as a remote server, CI worker, or terminal-only setup) without display sockets, container initialization, building, and non-graphical test suites must continue to function without error.
- **File Permissions**: When workspace files are modified inside the container by the container user, file ownership and permissions on the host system must remain accessible to the developer without root ownership lockouts.
- **Container Architecture**: The container definition should be portable across standard developer CPU architectures (x86_64 and aarch64).

## Requirements

### Functional Requirements

- **FR-001**: The repository MUST define a standard Development Container configuration under `.devcontainer/` conforming to the open Development Containers Specification.
- **FR-002**: The development container MUST provision all native toolchain dependencies required to build Cartridges, including C compilers, Meson, Ninja, and pkg-config.
- **FR-003**: The development container MUST provision the required GTK 4, Libadwaita, and GLib development libraries and header files.
- **FR-004**: The development container MUST provision the Blueprint compiler for compiling declarative UI templates.
- **FR-005**: The development container MUST provision the Python runtime (Python 3.12+) and fast package manager (`uv`) required for project dependencies.
- **FR-006**: The development container MUST automate post-creation lifecycle tasks to ensure Python dependencies and pre-commit hooks are initialized upon first launch.
- **FR-007**: The development container MUST support display socket passthrough configuration (Wayland / X11) to allow interactive GUI execution on supported hosts.
- **FR-008**: The development container configuration MUST support headless execution so automated test suites and linters can run without a display server.
- **FR-009**: The development container configuration SHOULD include recommended editor extensions (such as Python, Ruff, Meson, and Blueprint support) to streamline the developer experience.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A contributor can launch the development container and run a complete clean build in under 5 minutes on a standard developer connection.
- **SC-002**: 100% of standard build and test commands execute inside the container without requiring any package installations on the host system.
- **SC-003**: 100% of automated code quality gates (Pyright strict typing, Ruff linter, Ruff formatting, pre-commit) execute successfully inside the container.
- **SC-004**: The devcontainer configuration validates against the official Dev Container CLI and functions across common container engines (Docker, Podman).

## Assumptions

- Developers have a container engine (Docker, Podman) and a compatible devcontainer client (VS Code Dev Containers extension, GitHub Codespaces, or Devcontainer CLI) installed on their host system.
- The base container image can use a modern Linux distribution (such as Fedora or Ubuntu) or GNOME development base that packages recent GTK 4 and Libadwaita versions.
- Interactive GUI execution depends on host display server configuration; headless operations (compilation, automated tests, linters) do not require display passthrough.
