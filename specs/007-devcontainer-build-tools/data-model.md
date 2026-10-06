# Data Model: Development Container Configuration

**Feature**: Development Container for Build and Tooling
**Branch**: `feat/007-devcontainer-build-tools`
**Spec**: [spec.md](file:///var/home/samuel/Projects/cartridges/specs/007-devcontainer-build-tools/spec.md)

---

## Configuration Entities

### 1. DevContainer Specification (`devcontainer.json`)

Represents the declarative configuration recognized by Dev Container orchestrators (VS Code Dev Containers, Codespaces, DevPod, Devcontainer CLI).

| Field | Type | Description | Default / Example Value |
|---|---|---|---|
| `name` | `string` | Display name for the development container | `"Cartridges Development"` |
| `build` | `object` | Build context and Dockerfile definition | `{"dockerfile": "Dockerfile", "context": ".."}` |
| `remoteUser` | `string` | Non-root user within the container session | `"vscode"` |
| `containerUser` | `string` | User running container processes | `"vscode"` |
| `containerEnv` | `object` | Environment variables injected into container | `{"PAGER": "cat", "PYTHONUNBUFFERED": "1"}` |
| `mounts` | `array` | Volume and socket mounts (e.g. Wayland/X11 display) | `["source=/tmp/.X11-unix,target=/tmp/.X11-unix,type=bind,consistency=cached"]` |
| `postCreateCommand` | `string` | Lifecycle script executed after container creation | `"uv sync --dev && uv run pre-commit install"` |
| `customizations` | `object` | IDE-specific configurations and extensions | `{"vscode": {"extensions": [...]}}` |

### 2. Container Image Definition (`Dockerfile`)

Represents the multi-stage or layered build recipe provisioning system dependencies, development headers, and user accounts.

| Layer / Stage | Purpose | Key Artifacts / Packages Installed |
|---|---|---|
| **Base** | Foundation OS | `fedora:42` (or `fedora:latest`) |
| **System Toolchain** | Compilation and build engines | `gcc`, `gcc-c++`, `meson`, `ninja-build`, `pkg-config`, `git`, `make` |
| **GUI & Platform Headers** | GTK 4 and Libadwaita development | `gtk4-devel`, `libadwaita-devel`, `libadwaita-doc`, `gobject-introspection-devel` |
| **UI & Appstream Utilities** | Blueprint and metadata validation | `blueprint-compiler`, `appstream`, `appstream-devel`, `desktop-file-utils`, `gettext` |
| **Python Ecosystem** | Python runtime and package management | `python3`, `python3-devel`, `python3-pip`, `uv` binary copied to `/usr/local/bin/uv` |
| **User & Permissions** | Non-root developer environment | User `vscode` (UID/GID 1000) with passwordless `sudoers` rights |

### 3. Editor Customization Model (`customizations.vscode`)

Defines automated IDE extension recommendations for contributors using Visual Studio Code or OpenVSX-compatible editors.

| Extension ID | Name / Purpose |
|---|---|
| `charliermarsh.ruff` | Fast Python linting and formatting |
| `ms-pyright.pyright` | Strict static type checking |
| `ms-python.python` | Python language server and test runner |
| `mesonbuild.mesonbuild` | Meson build system syntax and language support |
| `freedomevenden.blueprint-gtk` | Blueprint declarative UI grammar and syntax |

---

## State Transitions & Lifecycle

```text
[Host Machine]
      │
      ▼
1. Container Build
   - Parse .devcontainer/Dockerfile
   - Install DNF packages (meson, ninja, gcc, gtk4-devel, libadwaita-devel, blueprint-compiler)
   - Provision user 'vscode' (UID 1000) with sudo privileges
   - Install 'uv' binary in /usr/local/bin
      │
      ▼
2. Container Start & Mount
   - Bind workspace mount at /workspaces/cartridges
   - Mount host display sockets (X11 / Wayland) if present
   - Drop root privileges to user 'vscode'
      │
      ▼
3. postCreateCommand Hook
   - Execute: uv sync --dev
   - Execute: uv run pre-commit install
      │
      ▼
4. Ready State (Interactive Development)
   - Developer can run: meson setup _build && meson compile -C _build
   - Developer can run: meson test -C _build -v
   - Developer can run: uv run pyright && uv run ruff check
   - Developer can inspect UI: adwaita-1-demo
```
