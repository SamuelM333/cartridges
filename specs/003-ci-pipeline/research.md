# Technical Research: Linux/Flatpak CI Pipeline, Release Packaging, and Nightly Caching

## 1. Overview & Objectives

This document establishes the architecture and design decisions for porting the CI/CD workflows from `cartridges-main` to the modern `rewrite` branch, scoped strictly to **Linux and Flatpak**:
1. Continuous Integration (`ci.yml`): Pre-commit formatting/hygiene, Pyright strict typing, Meson unit tests, and development Flatpak bundle compilation (`page.samuelm333.Cartridges.Devel.flatpak`).
2. Production Release Publishing (`publish-release.yml`): Tag-triggered packaging of the production Flatpak bundle (`page.samuelm333.Cartridges.flatpak`) attached to GitHub Releases with metadata-extracted changelogs.
3. Automated Nightly Builds (`nightly.yml`): Scheduled and manual dispatch workflow building `page.samuelm333.Cartridges.Devel.flatpak` and publishing to a rolling `nightly` release, while leveraging GitHub `actions/cache` to prevent redundant builds when the HEAD commit has not advanced.

## 2. Nightly Deduplication via `actions/cache`

### Decision
Use `actions/cache@v4` with an exact key based on the HEAD commit SHA:
`key: nightly-built-${{ github.sha }}`

### Mechanism & Workflow Flow
1. Check out repository with depth 1.
2. In a preliminary evaluation step:
   ```yaml
   - name: Check if commit was already built
     id: check-cache
     uses: actions/cache@v4
     with:
       path: .nightly-flag
       key: nightly-built-${{ github.sha }}
   ```
3. If `steps.check-cache.outputs.cache-hit == 'true'`:
   - Output `build_needed: false`.
   - Subsequent build and release steps skip execution (`if: steps.check-cache.outputs.cache-hit != 'true'`).
4. If `steps.check-cache.outputs.cache-hit != 'true'`:
   - Proceed to build Flatpak bundle.
   - Publish bundle to GitHub Release (tag `nightly`).
   - Create flag file `touch .nightly-flag`.
   - The cache action automatically saves the entry on workflow success or via an explicit `actions/cache/save@v4` step.

### Rationale
- Zero API rate limit consumption against GitHub Releases API.
- Zero git commits or tag mutations required just to check build status.
- Instant cache check (< 5 seconds) saves runner minutes and runner concurrency slots.

## 3. Flatpak Build Environment & Manifest Architecture

### A. Development Manifest (`flatpak/page.samuelm333.Cartridges.Devel.json`)
- Application ID: `page.samuelm333.Cartridges.Devel`
- Configuration option: `-Dprofile=development`
- Runtime: `org.gnome.Platform//master` (or 47), SDK: `org.gnome.Sdk//master` (or 47).
- Container: `bilelmoussaoui/flatpak-github-actions:gnome-47`.
- Builder Action: `flatpak/flatpak-github-actions/flatpak-builder@v6.5`.

### B. Production Manifest (`flatpak/page.samuelm333.Cartridges.json`)
- Application ID: `page.samuelm333.Cartridges`
- Configuration option: `-Dprofile=release`
- Runtime: `org.gnome.Platform//47`, SDK: `org.gnome.Sdk//47`.
- Container: `bilelmoussaoui/flatpak-github-actions:gnome-47`.
- Builder Action: `flatpak/flatpak-github-actions/flatpak-builder@v6.5`.

## 4. Release Metadata Extraction

### Decision
Extract release notes directly from `data/page.samuelm333.Cartridges.metainfo.xml.in` using a clean Python extraction step:

```python
import re
import sys
import textwrap

with open("data/page.samuelm333.Cartridges.metainfo.xml.in", encoding="utf-8") as f:
    content = f.read()

match = re.search(
    r"<release[^>]*>\s*<description[^>]*>\n([\s\S]*?)\s*</description>\s*</release>",
    content,
)
notes = textwrap.dedent(match.group(1)) if match else "Release notes not found."
with open("release_notes.md", "w", encoding="utf-8") as out:
    out.write(notes + "\n")
```

## 5. Security & GitHub Token Permissions

All workflows declare top-level permissions:
- `ci.yml`: `contents: read` (read-only for PR validation).
- `nightly.yml`: `contents: write` (for updating `nightly` release asset).
- `publish-release.yml`: `contents: write` (for publishing release assets).

Concurrency rules ensure that subsequent pushes cancel in-flight PR runs, while release jobs run atomically without collision.
