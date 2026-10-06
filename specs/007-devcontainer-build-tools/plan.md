# Implementation Plan: Development Container for Build and Tooling

**Branch**: `feat/007-devcontainer-build-tools` | **Date**: 2026-10-07 | **Spec**: [spec.md](file:///var/home/samuel/Projects/cartridges/specs/007-devcontainer-build-tools/spec.md)

**Input**: Feature specification from `specs/007-devcontainer-build-tools/spec.md`

---

## Summary

Define a standard Development Container under `.devcontainer/` using a modern Fedora container base image to provide a reproducible, one-click development environment. The container provisions all native compilation tools (`meson`, `ninja-build`, `gcc`), GTK 4 / Libadwaita development headers (`gtk4-devel`, `libadwaita-devel`, `libadwaita-doc`), UI compilation and validation utilities (`blueprint-compiler`, `appstream`, `desktop-file-utils`), and Python tooling (`uv` standalone manager, Pyright, Ruff, pre-commit).

---

## Technical Context

**Language/Version**: Container definition (Dockerfile and JSON) targeting Python 3.12+ with GTK 4 and Libadwaita

**Primary Dependencies**: Development Containers Specification, `fedora:42` base, `meson`, `ninja-build`, `gcc`, `gtk4-devel`, `libadwaita-devel`, `blueprint-compiler`, `uv`

**Storage**: Host workspace bind mount into `/workspaces/cartridges`

**Testing**: Container build verification (`podman build`), build pipeline test (`meson setup && meson compile`), test suite (`meson test -v`), and Python static analysis (`uv run pyright && uv run ruff check`)

**Target Platform**: Any system supporting standard OCI container runtimes (Docker, Podman, GitHub Codespaces, DevPod)

**Project Type**: Containerized development environment configuration

**Performance Goals**: Clean container build in under 3 minutes; non-interactive `postCreateCommand` setup in under 30 seconds

**Constraints**: Zero emojis in all documentation and files (Principle VI); non-root developer user execution (`vscode`) with passwordless sudo

**Scale/Scope**: Two configuration files: `.devcontainer/devcontainer.json` and `.devcontainer/Dockerfile`

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Relevance & Compliance | Status |
|---|---|---|
| **Principle I: Strict Typing & QA** | The container pre-installs `uv`, Pyright, Ruff, and pre-commit to enforce strict typing and formatting gates inside the container. | PASS |
| **Principle II: Modular Game Sources** | Not directly affected (infrastructure change). | PASS |
| **Principle III: Blueprint UI** | Pre-installs `blueprint-compiler` natively so developers can compile and validate `.blp` templates out of the box. | PASS |
| **Principle IV: Libadwaita & HIG (`adwaita-1-demo`)** | Pre-installs `libadwaita-devel`, providing `/usr/bin/adwaita-1-demo` as the canonical living reference for UI inspection. | PASS |
| **Principle V: Sandboxing & Asset Safety** | Uses non-root `vscode` user (UID 1000) with proper permissions to prevent permission escalation or file locking on the host. | PASS |
| **Principle VI: Emoji-Free Code & Docs** | All files, descriptions, and comments are verified 100% free of Unicode emoji characters. | PASS |

---

## Project Structure

### Documentation (this feature)

```text
specs/007-devcontainer-build-tools/
├── plan.md              # This implementation plan
├── research.md          # Technical research & architectural decisions
├── data-model.md        # DevContainer and Dockerfile configuration entities
├── quickstart.md        # Runnable verification and build test scenarios
├── contracts/
│   └── devcontainer-contract.md # Devcontainer schema and tool contracts
└── checklists/
    └── requirements.md  # Specification quality checklist
```

### Source Code Layout

```text
.devcontainer/
├── Dockerfile           # Layered container build installing compilers, GTK4/Adwaita, and uv
└── devcontainer.json    # Dev Container specification with user, mounts, extensions, and lifecycle hooks
```

**Structure Decision**: The devcontainer configuration is localized entirely under the standard `.devcontainer/` directory at the repository root, ensuring compatibility with GitHub Codespaces, VS Code Dev Containers, and the Dev Container CLI without polluting application source code.

---

## Complexity Tracking

No constitution violations or unjustified complexities. All tools directly mirror existing project dependencies and container setups.
