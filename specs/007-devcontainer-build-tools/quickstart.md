# Quickstart & Verification Guide: Development Container

**Feature**: Development Container for Build and Tooling
**Branch**: `feat/007-devcontainer-build-tools`
**Spec**: [spec.md](file:///var/home/samuel/Projects/cartridges/specs/007-devcontainer-build-tools/spec.md)

---

## Prerequisites

- A supported container engine: `docker` or `podman`.
- A devcontainer orchestrator: Visual Studio Code with the "Dev Containers" extension, GitHub Codespaces, DevPod, or the `@devcontainers/cli`.

---

## Verification Scenarios

### Scenario 1: Build the Container Image

Validate that the `.devcontainer/Dockerfile` builds cleanly without dependency resolution errors:

```bash
# Using devcontainer CLI
devcontainer build --workspace-folder .

# Or directly using podman / docker
podman build -t cartridges-dev -f .devcontainer/Dockerfile .
```

**Expected Outcome**: The container image compiles all layers successfully and exits with status code 0.

---

### Scenario 2: Verify Build Tool Availability

Inside the container shell, verify that all necessary build systems and compilers are installed:

```bash
# Verify compilation tools
meson --version
ninja --version
gcc --version
blueprint-compiler --version
pkg-config --modversion gtk4
pkg-config --modversion libadwaita-1

# Verify Python package manager
uv --version
```

**Expected Outcome**: All commands exit with status code 0 and output valid semantic version strings meeting the tool contract.

---

### Scenario 3: Build and Test Cartridges

Inside the container shell, run a complete clean build and automated test cycle:

```bash
# 1. Clean previous builds if any
rm -rf _build

# 2. Setup build directory
meson setup _build

# 3. Compile assets, resources, and templates
meson compile -C _build

# 4. Run automated test suite
meson test -C _build -v
```

**Expected Outcome**: Meson configuration detects all dependencies, compilation completes without warnings or errors, and `meson test` reports 3/3 tests passed.

---

### Scenario 4: Verify Python QA & Pre-Commit Gates

Inside the container shell, verify that code quality tools function in the containerized virtual environment:

```bash
# Run strict type checking
uv run pyright

# Run linter and formatting checks
uv run ruff check cartridges/ tests/
uv run ruff format --check cartridges/ tests/

# Run settings validation test
python3 tests/test_settings.py
```

**Expected Outcome**: All static analysis commands report clean passes (0 errors, 0 warnings).

---

### Scenario 5: Verify Canonical Reference Implementation

Verify that `adwaita-1-demo` is accessible for inspecting official Libadwaita patterns per Constitution Principle IV:

```bash
# Verify executable presence
test -x /usr/bin/adwaita-1-demo && echo "adwaita-1-demo is available"

# Verify gresource inspection capability
gresource list /usr/bin/adwaita-1-demo | head -n 10
```

**Expected Outcome**: The binary is present, executable, and resource schemas can be queried.
