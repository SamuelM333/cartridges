# Contract: Pull Request & Push CI Workflow (`ci.yml`)

## 1. Triggers
- **Push**: Branches `[main]`
- **Pull Request**: Target branch `main`

## 2. Permissions
```yaml
permissions:
  contents: read
```

## 3. Concurrency
```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

## 4. Jobs
1. **Quality Checks & Tests (`lint-and-test`)**:
   - Runs on: `ubuntu-26.04`
   - Container: `ghcr.io/flathub-infra/flatpak-github-actions:gnome-50` (with `--privileged`)
   - Toolchains provisioned via `pip3 install --break-system-packages ruff meson ninja git+https://gitlab.gnome.org/GNOME/blueprint-compiler.git`
   - Typelib & data paths configured via `GI_TYPELIB_PATH` and `XDG_DATA_DIRS` pointing to GNOME 50 Sdk
   - Validates AppStream metadata (`appstreamcli validate --no-net`).
   - Validates Desktop entry (`desktop-file-validate`).
   - Runs Meson test suite (`ninja -C _build test`).
2. **Development Flatpak Build (`flatpak`)**:
   - Runs on: `ubuntu-26.04`
   - Container: `ghcr.io/flathub-infra/flatpak-github-actions:gnome-50` (with `--privileged`)
   - Manifest: `flatpak/page.samuelm333.Cartridges.Devel.json`
   - Bundle output: `page.samuelm333.Cartridges.Devel.flatpak`
   - Artifact upload: `actions/upload-artifact@v4` publishes `page.samuelm333.Cartridges.Devel.flatpak` as a downloadable workflow artifact.
