# Technical Research: Linux/Flatpak CI Pipeline, Release Packaging, and Nightly Caching

## 1. Overview & Objectives

This document establishes the architecture and design decisions for porting the CI/CD workflows from `cartridges-main` to the modern `rewrite` branch, scoped strictly to **Linux and Flatpak**:
1. Continuous Integration (`ci.yml`): Pre-commit formatting/hygiene, Pyright strict typing, Meson unit tests, and development Flatpak bundle compilation (`page.samuelm333.Cartridges.Devel.flatpak`).
2. Production Release Publishing (`publish-release.yml`): Tag-triggered packaging of the production Flatpak bundle (`page.samuelm333.Cartridges.flatpak`) attached to GitHub Releases with metadata-extracted changelogs.
3. Automated Nightly Builds (`nightly.yml`): Scheduled and manual dispatch workflow building the production Flatpak bundle `page.samuelm333.Cartridges.flatpak` using the release manifest `flatpak/page.samuelm333.Cartridges.json` and publishing to a rolling `nightly` release, while leveraging GitHub `actions/cache` to prevent redundant builds when the HEAD commit has not advanced.

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
   - Proceed to build the production Flatpak bundle `page.samuelm333.Cartridges.flatpak` via `flatpak/page.samuelm333.Cartridges.json`.
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
- Runtime: `org.gnome.Platform//50`, SDK: `org.gnome.Sdk//50`.
- Modules: `blueprint-compiler` (git `v0.20.4`), `cartridges`, and `python3-pillow.json`.
- Container: `ghcr.io/flathub-infra/flatpak-github-actions:gnome-50`.
- Builder Action: `flatpak/flatpak-github-actions/flatpak-builder@v6.5`.

### B. Production Manifest (`flatpak/page.samuelm333.Cartridges.json`)
- Application ID: `page.samuelm333.Cartridges`
- Configuration option: `-Dprofile=release`
- Runtime: `org.gnome.Platform//50`, SDK: `org.gnome.Sdk//50`.
- Modules: `blueprint-compiler` (git `v0.20.4`), `cartridges`, and `python3-pillow.json`.
- Container: `ghcr.io/flathub-infra/flatpak-github-actions:gnome-50`.
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

## 6. Container Environment for CI Validation (`lint-and-test`)

### Decision
Use official `fedora:41` container image for the `lint-and-test` job in `.github/workflows/ci.yml`.

### Rationale
- **Native Distro Packages**: Fedora packages `blueprint-compiler`, `gtk4-devel`, `libadwaita-devel`, `glib2-devel`, `python3-gobject`, `python3-pillow`, `libmanette-devel`, `meson`, `ninja-build`, `appstream`, and `desktop-file-utils` directly in official repositories via `dnf`.
- **Standard Library and Typelib Paths**: GNOME introspection typelibs and GSettings schemas install to standard system locations (`/usr/lib64/girepository-1.0` and `/usr/share/glib-2.0/schemas`), completely eliminating the need for custom `GI_TYPELIB_PATH` or `XDG_DATA_DIRS` environment workarounds.
- **Clean Toolchain Setup**: Eliminates compiling `blueprint-compiler` from git via `pip3 install --break-system-packages git+...` during every CI run.
- **Environment Parity**: Directly mirrors the Fedora-based development environment mandated by the project Constitution (`gtk-dev` Distrobox).

### Alternatives Considered
- `ghcr.io/flathub-infra/flatpak-github-actions:gnome-50`: Kept for `flatpak-builder` jobs (`flatpak`, `build-release-flatpak`, `nightly`) where Flatpak runtimes and SDKs are needed, but discarded for `lint-and-test` due to lack of a system package manager and non-standard typelib paths.
- `ubuntu-latest`: Discarded because Ubuntu APT repositories do not ship native `blueprint-compiler` or the latest Libadwaita versions matching Cartridges requirements.
- `fedora:rawhide`: Evaluated, but `fedora:41` provides a stable, reproducible release image with all required GNOME 47+ libraries.

## 7. Pull Request Downloadable Artifact Upload

### Decision
Use `actions/upload-artifact@v4` in the `flatpak` job within `.github/workflows/ci.yml` to export `page.samuelm333.Cartridges.Devel.flatpak`.

### Rationale
- **Immediate Reviewer Feedback**: Reviewers and QA testers can immediately download and test the bundled development application using `flatpak install --user page.samuelm333.Cartridges.Devel.flatpak` directly from the Actions run summary without setting up local dev environments.
- **Fail-Safe Integrity**: Setting `if-no-files-found: error` ensures CI fails if the bundle was not generated.

### Alternatives Considered
- Relying on nightly builds only: Discarded because nightly builds only reflect merged commits on `main`, not pre-merge pull requests undergoing active review.
- Custom storage hosting: Discarded in favor of native GitHub Actions artifacts for zero extra infrastructure.

---

## 8. Host Runner Environment: ubuntu-26.04

### Decision
Standardize all workflow jobs (`runs-on: ubuntu-26.04`) on the modern Ubuntu 26.04 LTS GitHub Actions runner environment.

### Rationale
- **Modern Host Toolchains**: Ubuntu 26.04 provides the latest host Linux kernel, updated container daemon runtimes, modern host utilities, and security patches.
- **Consistency**: Eliminates ambiguities across workflows by specifying explicit LTS version pins (`ubuntu-26.04`) rather than floating alias names.

### Alternatives Considered
- `ubuntu-latest`: Currently an alias that will eventually roll over, but explicit `ubuntu-26.04` pinning ensures predictable environment configurations.
- `ubuntu-24.04` or `ubuntu-22.04`: Previous LTS generations, superseded by the Ubuntu 26 runner.

---

## 9. Nightly Production Mode Strategy

### Decision
Build and publish nightly releases in production mode using `flatpak/page.samuelm333.Cartridges.json` (application ID `page.samuelm333.Cartridges`, `-Dprofile=release`, bundle `page.samuelm333.Cartridges.flatpak`) instead of the development manifest.

### Rationale
- **End-to-End Environment Parity**: Nightly pre-release builds test the authentic production runtime profile, sandbox permissions, and official GSettings schemas.
- **Packaging Verification**: Validates production Meson build flags (`-Dprofile=release`) and metadata extraction on every nightly run, ensuring release readiness before tags are created.
- **User Consistency**: Nightly users test the exact same application identifier and visual branding as stable release users.

### Alternatives Considered
- *Keep development profile for nightly*: Discarded per user requirement that nightly releases run in prod mode. PR workflow checks (`ci.yml`) continue to build and upload preview development bundles for active development review.
