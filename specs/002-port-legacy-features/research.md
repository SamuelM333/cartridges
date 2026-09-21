# Research: Preferences Dialog, Flatpak Source, and SteamGridDB Integration

This document outlines the technical research, decisions, and patterns selected to port the legacy Preferences menu, Flatpak source, and SteamGridDB integration with maximum design reference to the main branch and zero new UI.

## 1. Preferences Dialog & Layout

### Decision
Port the legacy preferences controller and template as `Adw.PreferencesDialog` defined in Blueprint format, preserving the identical tab structures, pages, and groups from the legacy `main` branch (matching `data/gtk/preferences.blp` and `cartridges/preferences.py` exactly).

### Rationale
Ensures 100% layout and aesthetic parity as requested by the user ("no new ui", "take as much design reference as possible from main"). It leverages native Libadwaita standard components (PreferencesPage, PreferencesGroup, SwitchRow, ActionRow, EntryRow, ExpanderRow) which are fully HIG-compliant.

### Alternatives Considered
- **Refactoring the layout to use nested sub-dialogs**: Rejected because it diverges from the original layout and complicates navigation.
- **Procedural Python-based layout building**: Rejected because it violates Core Principle III (Blueprint-Driven Declarative UI).

---

## 2. GSettings Bindings & Toggles

### Decision
Bind all preferences switches and controls directly to their respective GSettings schemas using `SETTINGS.bind()`.
Toggles include:
- Behavior: `exit-after-launch` (Exit game toggle), `cover-launches-game` (Cover image launch toggle).
- Images: `high-quality-images` (High quality toggle).
- Import: `auto-import` (Automatic scans), `remove-missing` (Pruning uninstalled games), and source-specific switches/sub-toggles.
- SteamGridDB: `sgdb` (Enable SGDB), `sgdb-prefer` (Prefer SGDB over official), `sgdb-animated` (Prefer animated art).

### Rationale
GSettings provides robust, instantaneous synchronization between UI widgets and persistent application settings. Standard binding ensures settings are saved on-the-fly with zero boilerplate code.

### Alternatives Considered
- **Manual signal connection with explicit storage saving**: Rejected because it introduces unnecessary boilerplate and is highly prone to timing regressions compared to GSettings' native bidirectionally-bound properties.

---

## 3. Danger Zone Actions (Remove All, Reset App)

### Decision
Implement "Remove All Games" and "Reset App" within the Danger Zone group:
- **Remove All Games**: Marks all games in the library store as `removed = True`, saves updated JSON files, and updates the grid view. Provides an Adw.Toast with an "Undo" action.
- **Reset App**: Deletes the cartridges folder in user's XDG data, config, and cache directories (`DATA_DIR`, `CONFIG_DIR`, `CACHE_DIR`), resets all keys in `SETTINGS` and `STATE_SETTINGS` schemas, and exits the application.
- Both actions must trigger an explicit Gtk.AlertDialog modal to prevent accidental data loss.

### Rationale
Provides a robust system recovery option and clean slate management. The toast with "Undo" functionality provides an excellent user safety net for bulk deletion.

### Alternatives Considered
- **No confirmation modals**: Rejected because these are highly destructive operations, and proceeding without confirmation degrades the user experience.

---

## 4. Flatpak Game Source Discovery

### Decision
Implement `FlatpakSource` under `cartridges/sources/flatpak.py` subclassing the modular game source protocol:
- Scan standard flatpak application directories: `/var/lib/flatpak/app` (system-wide) and `~/.local/share/flatpak/app` (user-wide).
- Derive display names and icon names from the application's exported `.desktop` files.
- Launch games via `flatpak run <ID>` (or through Flatpak host command portals when Cartridges is sandboxed).

### Rationale
Adheres strictly to Core Principle II (Modular Game Sources), keeping scanning logic decoupled from the presentation layer.

### Alternatives Considered
- **Direct subprocess flatpak execution in sandbox**: Rejected because a Flatpak sandbox limits direct execution of host binaries; utilizing the host command portal (`org.freedesktop.portal.Flatpak` / `HostCommand`) is necessary for sandbox compliance.

---

## 5. SteamGridDB Asynchronous Fetching & Bulk Update

### Decision
All networking tasks (autocomplete lookups, grid cover image downloads, and bulk cover updates) must run asynchronously in background worker threads (via standard Python `concurrent.futures.ThreadPoolExecutor` or GLib threads), signaling the main GTK thread to update the UI on completion.
- When bulk cover update is clicked, run searches asynchronously for each game in the library.
- Show an active Adw.Spinner on the button and display a non-blocking download progress toast.

### Rationale
Keeps the GTK application loop highly responsive at a solid 60 FPS during intensive networking and network latency, in accordance with Core Principle V (Resource and Asset Sandboxing).

### Alternatives Considered
- **Synchronous urllib/requests queries**: Rejected because synchronous requests freeze the entire user interface, making the application appear unresponsive or crashed.

