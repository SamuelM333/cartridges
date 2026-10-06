# Quickstart & Validation Guide: System Color Scheme Synchronization

This guide details the procedure for building, executing, and validating the system color scheme synchronization feature end-to-end.

## 1. Prerequisites & Environment

- C/Meson/Blueprint builds: Run inside the `gtk-dev` container.
- Python QA and pre-commit checks: Run via `uv run` on the host.

## 2. Build & Compilation Verification

Verify that Blueprint templates, GSettings schema, and resources compile cleanly:

```bash
# In gtk-dev container
distrobox enter gtk-dev -- ninja -C _build
```

## 3. Automated Test Execution

Run the Meson automated test suite:

```bash
distrobox enter gtk-dev -- ninja -C _build test
```

## 4. Quality & Lint Verification

Execute static analysis and linting checks via `uv`:

```bash
# Strict type checking
uv run pyright

# Ruff linting
uv run ruff check cartridges/

# Ruff formatting check
uv run ruff format --check cartridges/
```

Verify zero emojis across the repository:

```bash
python3 -c "
import re, glob
emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
for path in glob.glob('specs/006-color-scheme/**', recursive=True) + glob.glob('cartridges/**', recursive=True):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            matches = emoji_pattern.findall(content)
            if matches:
                print(f'Emoji found in {path}: {matches}')
    except (IsADirectoryError, FileNotFoundError):
        pass
"
```

## 5. Interactive Verification Scenarios

### Scenario 1: Initial Launch in Dark Mode
1. Set host desktop appearance to Dark mode (`gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'`).
2. Launch Cartridges.
3. Verify that the window, headers, cards, and views render in dark appearance.

### Scenario 2: Initial Launch in Light Mode
1. Set host desktop appearance to Light mode (`gsettings set org.gnome.desktop.interface color-scheme 'default'`).
2. Launch Cartridges.
3. Verify that the window, headers, cards, and views render in light appearance.

### Scenario 3: Dynamic Theme Switching
1. With Cartridges running, toggle desktop appearance between Light and Dark mode.
2. Verify that Cartridges immediately updates its visual theme in real time without restart.

### Scenario 4: Clean Preferences Dialog
1. Open Preferences dialog (Ctrl+,).
2. Inspect the General tab.
3. Verify that only launcher behavior and image settings are present, with no appearance or color scheme toggle group.
