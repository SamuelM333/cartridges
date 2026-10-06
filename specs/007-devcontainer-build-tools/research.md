# Technical Research: Development Container for Build and Tooling

**Feature**: Development Container for Build and Tooling
**Branch**: `feat/007-devcontainer-build-tools`
**Spec**: [spec.md](file:///var/home/samuel/Projects/cartridges/specs/007-devcontainer-build-tools/spec.md)

---

## Technical Decisions

### Decision 1: Base Container Image & Package Ecosystem

- **Choice**: Fedora Linux base (`fedora:latest` / `fedora:42`)
- **Rationale**:
  - Cartridges is a modern Libadwaita / GTK4 application that requires up-to-date versions of GTK 4, Libadwaita (>= 1.5+), and `blueprint-compiler`.
  - Fedora's default package manager (`dnf`) provides all required native compilation tools (`meson`, `ninja-build`, `gcc`, `pkg-config`), native headers (`gtk4-devel`, `libadwaita-devel`, `libadwaita-doc`), translation tools (`gettext`), and metadata validation (`appstream`, `desktop-file-utils`) directly from official repositories without external PPAs.
  - Importantly, `libadwaita-devel` on Fedora packages `/usr/bin/adwaita-1-demo`, which directly satisfies Project Constitution Principle IV (subsection 7) for consulting the canonical reference implementation.
  - Matches the established project workflow documented in Constitution Section "Development Environment & Local Builds" which uses Fedora packages in the `gtk-dev` container.
- **Alternatives Considered**:
  - *Debian / Ubuntu base*: Debian Bookworm and Ubuntu 24.04 ship older versions of Libadwaita, lack `blueprint-compiler` in official repositories, and require external Git clones and builds.
  - *Arch Linux base*: Rolling release packages are bleeding edge, but container images have higher maintenance churn and larger image sizes.
  - *GNOME Flatpak SDK*: Excellent for Flatpak builds, but lacks a standard devcontainer interactive CLI experience with standard posix paths for `uv` and python virtualenvs.

### Decision 2: Python Tooling & Package Management

- **Choice**: System Python with standalone `uv` package manager (`ghcr.io/astral-sh/uv:latest` multi-stage copy or official standalone installer)
- **Rationale**:
  - The Cartridges development workflow uses `uv` for ultra-fast dependency resolution, pyright static typing, and ruff linting.
  - Storing `uv` in `/usr/local/bin/uv` allows both root and non-root users to execute `uv run` commands immediately upon login.
  - In `devcontainer.json`, `postCreateCommand` executes `uv sync --dev` and `uv run pre-commit install` to ensure developers are ready to code immediately.
- **Alternatives Considered**:
  - *System pip only*: Slower, conflicts with PEP 668 externally managed environment protections in modern distributions, and requires manual venv activation.
  - *Poetry / Conda*: Unnecessary overhead and deviates from the project's standardized `uv` toolchain.

### Decision 3: User Permissions & Non-Root Execution

- **Choice**: Provision a non-root developer user (`vscode` with UID 1000) with passwordless `sudo` access
- **Rationale**:
  - Conforms to the standard Development Containers Specification.
  - Prevents files created inside the container from being owned by root on the host machine filesystem.
  - Provides passwordless sudo so developers can install ad-hoc utilities if needed without friction.
- **Alternatives Considered**:
  - *Running as root*: Causes file permission issues on host bind mounts where created build artifacts and caches cannot be modified or cleaned by the host user.

### Decision 4: Graphical Display Passthrough & Headless Robustness

- **Choice**: Configure standard Wayland and X11 display socket mounts and environment variables with graceful headless fallback
- **Rationale**:
  - Developers on Linux workstations can run and test Cartridges visually using `python3 bin/cartridges` or inspect UI with `adwaita-1-demo`.
  - Setting display socket mounts in `devcontainer.json` (such as `/tmp/.X11-unix` and Wayland runtime directories) connects to the host display server.
  - For headless environments (e.g. GitHub Codespaces, CI runners, remote servers), missing display sockets do not block building, compiling, or executing Meson test suites.
- **Alternatives Considered**:
  - *Bundled VNC/Xvfb server*: Adds substantial image bloat (>500MB) and complexity. Native socket forwarding is cleaner and faster for local developer workstations, while headless testing covers remote containers.

### Decision 5: VS Code Extensions & Settings Integration

- **Choice**: Specify recommended extensions in `devcontainer.json` `customizations.vscode.extensions`:
  - `charliermarsh.ruff` (Python linting and formatting)
  - `ms-pyright.pyright` (Strict type checking)
  - `ms-python.python` (Python language support)
  - `mesonbuild.mesonbuild` (Meson build system syntax and tasks)
  - `freedomevenden.blueprint-gtk` (Blueprint declarative UI syntax highlighting)
- **Rationale**:
  - Immediate out-of-the-box IDE experience with zero manual configuration.
- **Alternatives Considered**:
  - *No recommended extensions*: Forces every new contributor to research and install extensions manually.
