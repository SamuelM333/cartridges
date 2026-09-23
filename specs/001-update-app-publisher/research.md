# Research: Update App Publisher & Flatpak FQN

This document outlines the technical research, decisions, and patterns selected to safely execute the publisher metadata and Flatpak FQN / Application ID migration.

## 1. Application ID & Flatpak FQN Rename

### Decision
Update the core Application ID and Flatpak FQN from `page.kramo.Cartridges` to `page.samuelm333.Cartridges`. Update the development profile ID to `page.samuelm333.Cartridges.Devel`.

### Rationale
To publish the active fork on Flathub or maintain proper system namespacing under the current maintainer, the Application ID must reflect the active GitHub publisher namespace (`samuelm333`).

### Alternatives Considered
- **Keep old ID (`page.kramo.Cartridges`)**: Rejected because it maintains branding of the archived upstream project, which violates the requirement to associate the fork with the active publisher.
- **Change only the user-facing metadata**: Rejected by the user's explicit request to update the Flatpak FQN.

---

## 2. Backward Compatibility and Transition Paths

### Decision
Configure the AppStream metainfo with `<replaces>` tags pointing to both the legacy and the immediate upstream identifiers:
```xml
<replaces>
  <id>hu.kramo.Cartridges</id>
  <id>page.kramo.Cartridges</id>
</replaces>
```

### Rationale
When an Application ID changes, software managers (like GNOME Software or KDE Discover) and package indices use the `<replaces>` tag to identify the new package as a direct successor, facilitating smooth transitions and updates.

### Alternatives Considered
- **No transitions**: Rejected because it leaves existing users orphaned or without a clean upgrade path.

---

## 3. Sandboxed D-Bus and GSettings Permissions

### Decision
Align GSettings schema IDs and paths, D-Bus service names, and output file names with the new Application ID:
- GSettings schema path: `/page/samuelm333/Cartridges/` (and `/page/samuelm333/Cartridges/Devel/`)
- D-Bus service name: `page.samuelm333.Cartridges` (and `page.samuelm333.Cartridges.Devel`)

### Rationale
Under Flatpak sandbox security constraints, the sandbox only grants GSettings and D-Bus access permissions automatically if the schema ID and D-Bus names match the Flatpak Application ID exactly.

### Alternatives Considered
- **Keep old GSettings path**: Rejected because the sandbox would block the renamed application from reading or writing its settings.

---

## 4. Desktop Game Source Blacklisting

### Decision
In `cartridges/sources/desktop.py`, update `_FILE_BLACKLIST` and `_FLATPAK_ID_BLACKLIST` to block both the old and new App IDs:
- Add `page.samuelm333.Cartridges.*` to `_FILE_BLACKLIST`.
- Add `page.samuelm333.Cartridges` and `page.samuelm333.Cartridges.Devel` to `_FLATPAK_ID_BLACKLIST`.
- Retain existing `page.kramo.Cartridges` and `hu.kramo.Cartridges` blacklists.

### Rationale
Cartridges must never show itself as an importable game. Maintaining blacklists for both old and new IDs ensures that old shortcuts or caches from prior installations are also blacklisted.

### Alternatives Considered
- **Only blacklist the new ID**: Rejected because if a user has legacy desktop entries on disk, Cartridges would incorrectly import its own legacy launcher.

---

## 5. Non-Scrubbing of Author Credits

### Decision
1. Retain "kramo" inside the About Dialog's `authors` list.
2. Add "samuelm333" as the current main developer/maintainer.
3. Keep all file-level SPDX copyright headers intact for historical files.

### Rationale
Honors open-source license attribution requirements and the user's explicit directive to only update publishing-relevant metadata without scrubbing historical author attributions.

### Alternatives Considered
- **Overwrite developer name in About Dialog entirely**: Rejected because it scrubs historical credit, violating user instructions.
