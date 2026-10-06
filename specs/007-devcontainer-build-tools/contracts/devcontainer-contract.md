# Interface & Environment Contracts: Development Container

**Feature**: Development Container for Build and Tooling
**Branch**: `feat/007-devcontainer-build-tools`
**Spec**: [spec.md](file:///var/home/samuel/Projects/cartridges/specs/007-devcontainer-build-tools/spec.md)

---

## 1. Dev Container Specification Schema (`devcontainer.json`)

The `.devcontainer/devcontainer.json` file must validate against the standard Dev Containers schema:
`https://raw.githubusercontent.com/devcontainers/spec/main/schemas/devContainer.schema.json`

### Required Top-Level Properties

```json
{
  "$schema": "https://raw.githubusercontent.com/devcontainers/spec/main/schemas/devContainer.schema.json",
  "name": "Cartridges Development",
  "build": {
    "dockerfile": "Dockerfile",
    "context": ".."
  },
  "remoteUser": "vscode",
  "containerUser": "vscode",
  "postCreateCommand": "uv sync --dev && uv run pre-commit install",
  "customizations": {
    "vscode": {
      "extensions": [
        "charliermarsh.ruff",
        "ms-pyright.pyright",
        "ms-python.python",
        "mesonbuild.mesonbuild",
        "freedomevenden.blueprint-gtk"
      ]
    }
  }
}
```

---

## 2. Tool Availability Contract (CLI Environment)

When a developer or automated process opens a shell inside the running container, the following binaries and library paths MUST be resolvable on `$PATH` and `$PKG_CONFIG_PATH`:

| Command / Tool | Minimum Version | Contract Verification Command | Expected Outcome |
|---|---|---|---|
| `meson` | `>= 1.0.0` | `meson --version` | Exits 0, outputs semantic version |
| `ninja` | `>= 1.10.0` | `ninja --version` | Exits 0, outputs version |
| `gcc` | `>= 13.0` | `gcc --version` | Exits 0, C compiler available |
| `pkg-config (gtk4)` | `>= 4.14` | `pkg-config --modversion gtk4` | Exits 0, version `>= 4.14` |
| `pkg-config (libadwaita-1)` | `>= 1.5` | `pkg-config --modversion libadwaita-1` | Exits 0, version `>= 1.5` |
| `blueprint-compiler` | `>= 0.14` | `blueprint-compiler --version` | Exits 0, prints compiler version |
| `adwaita-1-demo` | Any | `test -x /usr/bin/adwaita-1-demo` | Exits 0, binary executable present |
| `appstreamcli` | Any | `appstreamcli --version` | Exits 0, validation tool present |
| `desktop-file-validate` | Any | `desktop-file-validate --version` | Exits 0, validator present |
| `python3` | `>= 3.12` | `python3 --version` | Exits 0, Python runtime present |
| `uv` | `>= 0.4.0` | `uv --version` | Exits 0, standalone uv manager |

---

## 3. Lifecycle Hook Contract

### `postCreateCommand` Contract

- **Invocation**: Triggered automatically once container provisioning and workspace bind mounting are complete.
- **Environment**: Executed as `remoteUser` (`vscode`) with working directory set to `/workspaces/cartridges`.
- **Command String**: `uv sync --dev && uv run pre-commit install`
- **Behavior**:
  - Non-interactive (MUST NOT prompt for confirmation or credentials).
  - Populates `.venv` with development dependencies specified in `pyproject.toml`.
  - Installs git hook scripts in `.git/hooks/` for automated pre-commit gating.
  - Returns exit code 0 on successful completion.
