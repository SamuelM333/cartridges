# Contract: Pull Request & Push CI Workflow (`ci.yml`)

## 1. Triggers
- **Push**: Branches `[rewrite]`
- **Pull Request**: Target branch `rewrite`

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
   - Runs pre-commit hooks (Ruff, Pyright strict mode, Blueprint compiler format, Meson format, Prettier).
   - Validates AppStream metadata (`appstreamcli validate`).
   - Validates Desktop entry (`desktop-file-validate`).
   - Validates GSettings schemas (`glib-compile-schemas`).
   - Runs Meson test suite (`ninja -C _build test`).
2. **Development Flatpak Build (`flatpak`)**:
   - Runs on: `ubuntu-latest`
   - Container: `bilelmoussaoui/flatpak-github-actions:gnome-47` (with `--privileged`)
   - Manifest: `flatpak/page.samuelm333.Cartridges.Devel.json`
   - Bundle output: `page.samuelm333.Cartridges.Devel.flatpak`
