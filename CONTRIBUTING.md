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

Install the git hook once in every clone or container, so the same checks run when you commit:

```bash
uv run pre-commit install
```

The devcontainer does this for you.

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

Every script in `tests/` is a meson test. To run one on its own, for example while debugging:

```bash
python3 tests/test_logs.py
```

A new test script must be added to `tests/meson.build`, or CI will not run it.

## Speckit workflow

Feature specifications and implementation plans are managed with [Speckit](https://github.com/github/spec-kit). Feature artifacts are stored under `specs/`, while project-wide development principles live in `.specify/memory/constitution.md`.

For planned work, use the [Speckit workflow](https://github.github.io/spec-kit/quickstart.html#recommended-process) to clarify or create the specification, generate a plan and task list, and implement the tasks in order. Keep the artifacts aligned with the code as requirements or implementation details change. The repository's `.claude/skills/` directory contains the available Speckit workflows.

## Committing and pull requests

Commit with `uv run git commit`, inside the `gtk-dev` container if you use it, so the pre-commit hook runs with the project's tools. Do not skip the hook with `--no-verify`: fix what it reports. If a check already fails on `main`, fix it minimally in your pull request and say so in the description, or fix it in a separate pull request first.

Before committing, check for emoji:

```bash
python3 .specify/scripts/bash/check-emojis.py            # unstaged changes and new files
python3 .specify/scripts/bash/check-emojis.py --cached   # staged changes
```

Emoji are fine as functional content that a specification asks for, such as an icon picker or a notification. Avoid them in comments, documentation, specifications, and commit messages.

Work produced with a coding agent must say so. End the commit message with a `Co-Authored-By:` trailer naming the agent and, when known, the model, and end the pull request description with a line saying it was generated with the agent and linking to the tool.

When you implement a feature with `/speckit-implement`, the work is not finished until its pull request is open. Once the tasks are done and the checks pass, push the feature branch and run `gh pr create` into `main`. Use a conventional commit style title, summarize the change in the body, link `specs/00X-name/`, and list any verification you did not perform.

CI runs the same pre-commit checks and the meson tests on every pull request.

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
