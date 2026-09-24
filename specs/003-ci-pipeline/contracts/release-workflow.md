# Contract: Production Release Workflow (`publish-release.yml`)

## 1. Triggers
- **Push**: Tags `v*` (e.g. `v2.0.0`)

## 2. Permissions
```yaml
permissions:
  contents: write
```

## 3. Concurrency
```yaml
concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false
```

## 4. Release Packaging & Assets
- **Linux Flatpak Bundle**:
  - Container: `ghcr.io/flathub-infra/flatpak-github-actions:gnome-50`
  - Manifest: `flatpak/page.samuelm333.Cartridges.json` (Profile: release, ID: `page.samuelm333.Cartridges`)
  - Asset filename: `page.samuelm333.Cartridges.flatpak`

## 5. Release Note Extraction
- Notes extracted directly from `<releases><release version="...">...` in `data/page.samuelm333.Cartridges.metainfo.xml.in`.
- Generated file `release_notes.md` used as `body_path` for `softprops/action-gh-release@v2.2.2`.
