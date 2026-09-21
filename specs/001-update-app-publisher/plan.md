# Implementation Plan: Update App Publisher Metadata

**Branch**: `001-update-app-publisher` | **Date**: 2026-09-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-update-app-publisher/spec.md`

## Summary

This feature updates the application's publisher metadata from `kramo` to `samuelm333` and migrates the Flatpak Fully Qualified Name (FQN) / Application ID to `page.samuelm333.Cartridges`. All system file dependencies, GSettings paths, D-Bus service registrations, icon files, and desktop entry structures will be renamed to align with this new FQN namespace. At the same time, we strictly enforce that historical developer credit ("kramo") is preserved in the application credits (About Dialog) and source copyright headers, and that only publishing-related metadata is overwritten.

---

## Technical Context

- **Language/Version**: Python (>= 3.10)
- **Primary Dependencies**: PyGObject (Gtk 4, Adw 1, Manette 0.2)
- **Storage**: GSettings (using the application's unique reverse-DNS namespace)
- **Testing**: Meson built-in unit tests (`desktop-file-validate`, `glib-compile-schemas`, `appstreamcli validate`)
- **Target Platform**: Flatpak sandbox / Linux Desktop Environments
- **Project Type**: Desktop Application
- **Performance Goals**: Instant D-Bus activation and settings loading (no regressions)
- **Constraints**: Flatpak sandbox security rules require GSettings schema ID and D-Bus service name to match the application ID exactly.
- **Scale/Scope**: System-level integration configuration files, desktop launcher templates, translation catalogs, and blacklist filters.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution (v1.4.0) contains strict rules. Here is our assessment:

- **I. Strict Typing & Quality Assurance**: All Python changes (mainly blacklist additions in `desktop.py`) must pass Pyright and Ruff check/format with no exceptions.
- **II. Modular Game Sources**: The desktop source module (`desktop.py`) must handle self-blacklisting using its own updated package boundary without hardcoding UI logic.
- **III. Blueprint-Driven Declarative UI**: No Blueprint files are modified for this task. The existing about dialog template remains unmodified.
- **IV. GNOME HIG & Desktop Integration**: Renaming GSettings and D-Bus identifiers is mandatory for native sandboxed desktop integration under GNOME/Flatpak.
- **V. Resource and Asset Sandboxing**: The GResource templates are preserved, with only asset prefixes in the icon catalog updated.
- **VI. Emoji-Free Code and Documentation**: No emojis are used in the specification, research, design, planning, or any code files.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-update-app-publisher/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Research findings and FQN transition decisions
├── data-model.md        # GSettings schemas and desktop/D-Bus identifier definitions
├── quickstart.md        # Run and build validation guide
└── checklists/
    └── requirements.md  # Specification quality checklist
```

### Source Code & Files to Modify

```text
cartridges/
├── sources/
│   └── desktop.py       # [MODIFY] Blacklist old and new Application IDs
meson.build              # [MODIFY] Update release/devel app ID and prefix configuration
data/
├── meson.build          # [MODIFY] Reference renamed build-template files
├── page.samuelm333.Cartridges.desktop.in       # [NEW] Renamed desktop template
├── page.samuelm333.Cartridges.gschema.xml.in   # [NEW] Renamed GSettings schema template
├── page.samuelm333.Cartridges.metainfo.xml.in  # [NEW] Renamed AppStream metainfo template
├── page.samuelm333.Cartridges.service.in       # [NEW] Renamed D-Bus service template
├── icons/
│   ├── page.samuelm333.Cartridges.svg          # [NEW] Renamed main icon asset
│   ├── page.samuelm333.Cartridges-symbolic.svg # [NEW] Renamed symbolic icon asset
│   ├── page.samuelm333.Cartridges.Devel.svg    # [NEW] Renamed devel icon asset
│   └── page.samuelm333.Cartridges.Devel-symbolic.svg # [NEW] Renamed devel symbolic icon asset
├── page.kramo.Cartridges.desktop.in       # [DELETE]
├── page.kramo.Cartridges.gschema.xml.in   # [DELETE]
├── page.kramo.Cartridges.metainfo.xml.in  # [DELETE]
├── page.kramo.Cartridges.service.in       # [DELETE]
└── icons/
    ├── page.kramo.Cartridges.svg          # [DELETE]
    ├── page.kramo.Cartridges-symbolic.svg # [DELETE]
    ├── page.kramo.Cartridges.Devel.svg    # [DELETE]
    └── page.kramo.Cartridges.Devel-symbolic.svg # [DELETE]
flatpak/
├── page.samuelm333.Cartridges.Devel.json  # [NEW] Renamed flatpak manifest
└── page.kramo.Cartridges.Devel.json       # [DELETE]
po/
└── POTFILES.in          # [MODIFY] Update resource file paths for translation
README.md                # [MODIFY] Update icon asset link
```

**Structure Decision**: Single project layout matching Option 1. The FQN transition requires modifying build setup files, translating file names, and updating metadata templates.

---

## Proposed Changes

Grouped by component area:

### Build System & Package Manifests

#### [MODIFY] [meson.build](file:///var/home/samuel/Projects/cartridges/meson.build)
- Update `app_id` and `prefix` string values for both release and development profiles under the new `samuelm333` namespace.

#### [MODIFY] [data/meson.build](file:///var/home/samuel/Projects/cartridges/data/meson.build)
- Rename references of input configuration files from `page.kramo.Cartridges.*` to `page.samuelm333.Cartridges.*`.

#### [NEW] [page.samuelm333.Cartridges.Devel.json](file:///var/home/samuel/Projects/cartridges/flatpak/page.samuelm333.Cartridges.Devel.json)
- Copy the flatpak manifest to the new name and update occurrences of `id` and paths to reference `page.samuelm333.Cartridges.Devel`. Ensure relative source path `"path": "../"` is preserved so GNOME Builder can parse the repository structure and compile/run the development profile out-of-the-box.

#### [DELETE] [page.kramo.Cartridges.Devel.json](file:///var/home/samuel/Projects/cartridges/flatpak/page.kramo.Cartridges.Devel.json)
- Remove the deprecated flatpak manifest.

### Metadata & Desktop Integration Templates

#### [NEW] [page.samuelm333.Cartridges.desktop.in](file:///var/home/samuel/Projects/cartridges/data/page.samuelm333.Cartridges.desktop.in)
- Create from legacy template.

#### [NEW] [page.samuelm333.Cartridges.gschema.xml.in](file:///var/home/samuel/Projects/cartridges/data/page.samuelm333.Cartridges.gschema.xml.in)
- Create from legacy template.

#### [NEW] [page.samuelm333.Cartridges.metainfo.xml.in](file:///var/home/samuel/Projects/cartridges/data/page.samuelm333.Cartridges.metainfo.xml.in)
- Create from legacy template. Update developer ID to `page.samuelm333` and add the `<replaces>` elements:
  ```xml
  <replaces>
    <id>hu.kramo.Cartridges</id>
    <id>page.kramo.Cartridges</id>
  </replaces>
  ```
- Keep the `kramo` attribution in place.

#### [NEW] [page.samuelm333.Cartridges.service.in](file:///var/home/samuel/Projects/cartridges/data/page.samuelm333.Cartridges.service.in)
- Create from legacy template.

#### [DELETE] [page.kramo.Cartridges.*](file:///var/home/samuel/Projects/cartridges/data/)
- Remove the deprecated legacy template files from `data/`.

### Graphics & Icon Assets

#### [NEW] [page.samuelm333.Cartridges.*](file:///var/home/samuel/Projects/cartridges/data/icons/)
- Rename the four icon SVG files in `data/icons/` to use the `page.samuelm333.Cartridges` prefix.

#### [DELETE] [page.kramo.Cartridges.*](file:///var/home/samuel/Projects/cartridges/data/icons/)
- Remove the deprecated legacy icon files from `data/icons/`.

### Source Code Adjustments

#### [MODIFY] [cartridges/sources/desktop.py](file:///var/home/samuel/Projects/cartridges/cartridges/sources/desktop.py)
- Update `_FILE_BLACKLIST` and `_FLATPAK_ID_BLACKLIST` to include `page.samuelm333.Cartridges` and `page.samuelm333.Cartridges.Devel` patterns alongside the legacy `kramo` and `hu` entries.

---

## Verification Plan

### Automated Tests
- `meson setup _build -Dprofile=release`: Verifies that meson setup can complete successfully and configures schemas.
- `meson compile -C _build`: Verifies that schemas compile and resource bundles compile correctly.
- `meson test -C _build`: Validates compiled AppStream metainfo, GSettings schema files, and Desktop launchers.

### Manual Verification
- Launch the application manually via `python3 -m cartridges`.
- Open the Gtk about dialog to verify:
  - Main developer website points to samuelm333's repository.
  - Previous developers are acknowledged.
- Ensure the application cannot import itself as a desktop game.
- **GNOME Builder Integration**:
  - Open the project workspace in GNOME Builder.
  - Builder should automatically detect and load `flatpak/page.samuelm333.Cartridges.Devel.json`.
  - Compile and execute the application using GNOME Builder's run pipeline to ensure out-of-the-box build compatibility.
