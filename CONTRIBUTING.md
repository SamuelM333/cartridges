# Contributing

## Code

Please follow the [code style](#code-style) and project guidance in the repository's [Speckit constitution](.specify/memory/constitution.md).

### Adding a feature

Open an issue in the [GitHub repository](https://github.com/SamuelM333/cartridges/issues) to discuss the feature with the maintainers before starting substantial work.

### Fixing a bug

Fork the [GitHub repository](https://github.com/SamuelM333/cartridges), make your changes, and open a pull request. Mention the related issue if one exists.

## Translations

### Weblate

The project can be translated on [Weblate](https://hosted.weblate.org/engage/cartridges/).

### Manually

1. Clone the repository.
2. If it is not already there, add your language to `po/LINGUAS`.
3. Create a translation from `po/cartridges.pot` using a translation editor such as [Poedit](https://poedit.net/).
4. Save the file as `[YOUR LANGUAGE CODE].po` in `po/`.
5. Open a pull request with your translation.

# Building

Cartridges is a Linux application built with Meson. GNOME Builder can also be used to clone the repository and build the project.

## GNOME Builder
1. Install [GNOME Builder](https://flathub.org/apps/org.gnome.Builder).
2. Click "Clone Repository" with `https://git.kramo.page/cartridges.git` as the URL.
3. Click on the build button (hammer) at the top.

## Mason
```bash
git clone https://git.kramo.page/cartridges.git
cd cartridges
meson setup build
ninja -C build install
```

## Development environment

The project uses [uv](https://docs.astral.sh/uv/) to manage Python development tools. Install `uv`, then sync the development dependencies from the repository root:

```bash
uv sync --group dev
```

The development dependency group includes Ruff, Pyright, Blueprint Compiler, and the other Python tools used by the project.

## Build with Meson

Install the system build dependencies required by the project, then configure and build it:

```bash
meson setup _build
ninja -C _build
```

To run the test suite:

```bash
ninja -C _build test
```

## Speckit workflow

Feature specifications and implementation plans are managed with [Speckit](https://github.com/github/spec-kit). Feature artifacts are stored under `specs/`, while project-wide development principles live in `.specify/memory/constitution.md`.

For planned work, use the [Speckit workflow](https://github.github.io/spec-kit/quickstart.html#recommended-process) to clarify or create the specification, generate a plan and task list, and implement the tasks in order. Keep the artifacts aligned with the code as requirements or implementation details change. The repository's `.agents/skills/` directory contains the available Speckit workflows.

# Code style

Python code is formatted and linted with [Ruff](https://docs.astral.sh/ruff/) and checked with [Pyright](https://microsoft.github.io/pyright/). Blueprint templates and project configuration should follow the checks configured in `.pre-commit-config.yaml`.

Run the Python lint and format checks with:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

Run the repository's pre-commit checks with:

```bash
uv run pre-commit run --all-files
```
