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
All networking tasks (autocomplete lookups, grid cover image downloads, and bulk cover updates) must run asynchronously in background worker threads (via standard Python `asyncio.to_thread`), signaling the main GTK thread to update the UI on completion.
- When bulk cover update is clicked, run searches asynchronously for each game in the library.
- Show an active Adw.Spinner on the button and display a non-blocking download progress toast upon completion.

### Rationale
Keeps the GTK application loop highly responsive at a solid 60 FPS during intensive networking and network latency, in accordance with Core Principle V (Resource and Asset Sandboxing).

### Alternatives Considered
- **Synchronous urllib/requests queries**: Rejected because synchronous requests freeze the entire user interface, making the application appear unresponsive or crashed.

---

## 6. SteamGridDB Real-Time Progress, Error Notifications, and Packaging

### Decision
1. **Real-Time Progress Section**: Add `Adw.ActionRow sgdb_progress_row` containing a `Gtk.ProgressBar` directly beneath "Update Covers" in `cartridges/ui/preferences.blp`. Update the row title (`Updating: <game_name>`), row subtitle (`<index>/<total> games`), and progress bar fraction continuously in real time as each game is processed.
2. **Explicit Error Handling & Validation**: Validate the SteamGridDB API key before querying. On missing key or HTTP 401 Unauthorized (`SgdbAuthError`), log a warning, trigger an immediate notification toast (`Invalid SteamGridDB API key`), and abort early without repeated failures across remaining games.
3. **Automatic Startup Fetching**: Hook `_check_auto_fetch_sgdb_covers` into `Application.do_startup()` in `cartridges/application.py`. If SteamGridDB is enabled and a valid API key is set, spawn a background asyncio task to download missing covers for uncovered games.
4. **Meson Package Installation**: Include `cartridges/utils` in `cartridges/meson.build` via `install_subdir('utils', install_dir: python.get_install_dir() / 'cartridges')` and include `cartridges/utils/__init__.py`.
5. **Standard Logging**: Initialize `logging.basicConfig(level=logging.INFO, ...)` in `cartridges/__main__.py` to surface request and error logs cleanly in GNOME Builder.

### Rationale
Satisfies FR-020, FR-025, SC-012, and User Story 8 Scenarios 3 & 4. Resolves `ModuleNotFoundError` in Flatpak sandboxes, eliminates silent failure swallowing, and provides visual and diagnostic feedback for users and developers.

### Alternatives Considered
- **Modal dialog for progress**: Rejected as intrusive and contrary to GNOME HIG non-blocking patterns.
- **Silent failure on 401**: Rejected because users had no indication of why cover updating failed.

---

## 7. Legacy Cover Overlay Buttons in Game Edit Page with Staged Apply & Reversibility

### Decision
1. **Legacy Cover Overlay Layout in Edit Page**:
   - Limit cover editing interactions strictly to the Edit Game page (hidden when viewing standard game details).
   - In `cartridges/ui/game-details.blp`, attach direct overlay action buttons over the cover in the Edit pane matching the legacy layout from `cartridges-main`:
     - **Pencil Button** (`document-edit-symbolic`): Opens `Gtk.FileDialog` to manually choose a local image.
     - **Globe Button** (`globe-symbolic`): Opens `CoverPicker` to search and pick from SteamGridDB (returning up to 10 artwork choices).
     - **Trash Can Button** (`user-trash-symbolic`): Removes the current cover image (visible when a cover is set, with crossfade transition).
2. **Staged Apply & Full Reversibility**:
   - Choosing a local image, selecting a SteamGridDB cover, or clicking the trash can button stages the modification in memory:
     - The staged cover texture/paintable is displayed immediately on the cover widget in the edit view.
     - Staged cover data or temp path is held in an internal state attribute on `GameDetails` (e.g. `_staged_cover_path: Path | None`, `_staged_cover_action: str | None` such as `"set"`, `"remove"`, or `"unchanged"`).
     - No files are written, replaced, or deleted in `COVERS_DIR` until the user explicitly commits changes.
   - **Clicking "Cancel"**: Reverts all staged cover changes without writing to disk, restoring the original `game.cover` paintable and clearing any staging state.
   - **Clicking "Apply"**: Commits the staged cover modification:
     - If staged to remove: unlinks cover files (`.tiff`, `.gif`) for `game.game_id` and sets `game.cover = None`.
     - If staged to set: processes the image (resizing, converting to TIFF/GIF as appropriate) and writes to `COVERS_DIR / f"{game.game_id}.tiff"` (or `.gif`), preserving original backup if applicable, then updates `game.cover`.
3. **Dismissable Download Status Banner**:
   - In `cartridges/ui/preferences.blp`, beneath the "Update Covers" progress row, include a dismissable `Adw.ActionRow` (`sgdb_status_row`) with a close/dismiss button (`window-close-symbolic`).
   - When the bulk download process ends (or fails), hide the progress bar row, reveal the status banner with the completion summary (e.g. "Finished updating covers: 12/15 successful"), and keep it visible until the user clicks dismiss or a new update starts.

### Rationale
- Restoring the proven legacy cover overlay layout avoids awkward nested popovers, restores instantaneous visual affordance for the primary actions (trash, manual choose, SteamGridDB fetch), and matches user mental models.
- Deferring disk changes until "Apply" guarantees full transactional reversibility: accidental clicks or changes can simply be cancelled without corrupting or permanently losing the user's existing cover art.

### Alternatives Considered
- **Immediate file writing on image selection**: Rejected because user explicitly required that changes only apply when clicking Apply, and must be reversible on Cancel.
- **GTK PopoverMenu with path entries**: Replaced per explicit user directive to revert back to the legacy Edit view cover controls.

---

## 8. Browse Files Icon, Title Validation, and Cover Persistence on Apply

### Decision
1. **Button Icons & Tooltips in Edit Mode**:
   - Change manual file picker icon in `cartridges/ui/game-details.blp` from pencil (`document-edit-symbolic`) to folder (`folder-symbolic`) with tooltip `_("Browse files")`.
   - Update SteamGridDB button tooltip to `_("Browse SteamGridDB")`.
2. **Always Active Local Cover & Adding Games**:
   - The Browse files folder button is always active in Edit mode, including when creating/adding a new game (`game is None`).
   - Staged images generate a temporary file with a unique ID (or `temp_<game_id>` / `temp_<uuid>`).
3. **SteamGridDB Title Validation**:
   - When the SteamGridDB button is clicked, check if `self.name_entry.get_text().strip()` is non-empty.
   - If empty, apply `.add_css_class("error")` to `self.name_entry`, call `self.name_entry.grab_focus()`, and return without launching the picker.
   - Connect `notify::text` on `name_entry` to clear the `error` CSS class as soon as the user enters text.
   - Support `CoverPicker` without requiring an existing `Game` instance by accepting `game_name` for new game additions.
4. **Cover Persistence on Apply**:
   - In `_apply()`, prevent `notify::game` from synchronously triggering `_on_game_changed()` and discarding `_staged_cover_temp_path` by setting an `_is_applying` guard and caching staged cover actions before updating `self.game = self.game_editable.game`.
   - Ensure the staged temporary file is moved to `COVERS_DIR / f"{self.game.game_id}{ext}"`, linked to `self.game.cover`, and persisted cleanly.

### Rationale
Satisfies FR-026, FR-029, and SC-015, ensuring immediate file staging without crashes when adding new games, preventing invalid SteamGridDB queries with empty game titles, and preventing data loss when saving.

### Alternatives Considered
- **Disabling the SteamGridDB button when title is empty**: Rejected because user explicitly requested: "only after the title value is populated, otherwise show the title field in red error", requiring visual error indication and focus on click.
- **Requiring game creation before cover staging**: Rejected because users frequently set the cover while adding a new game before clicking Add/Apply.

---

## 9. SteamGridDB Cover Picker Aspect Ratio, Dialog Sizing & Visual Framing

### Decision
1. **Scaled Selection Dialog Size Relative to Main Window**:
   - The main window default dimensions are 920x700px.
   - Configure `CoverPicker` in `cartridges/ui/cover_picker.blp` with a generous content area: `content-width: 800; content-height: 580;` (scaled proportionally relative to the main application window).
2. **Full Image Visibility & Aspect Ratio Alignment (2:3)**:
   - Configure preview images in `CoverPicker` using the exact 2:3 ratio (`cover.WIDTH / cover.HEIGHT = 200 / 300`) matching `Cover` in Game Details.
   - Use `Gtk.ContentFit.CONTAIN` on the preview `Gtk.Picture` and set proportional request dimensions (e.g. 160x240, or 140x210) within the card button, or set `content_fit: contain` so that 100% of the artwork and its entire borders/perimeter are fully visible without any edge or border clipping.
   - Remove outer clip/cut conflicts so border lines on the image remain pristine.
3. **Remove All Text Labels**:
   - Eliminate both "Static" and "Animated" text labels below the cover previews in `CoverPicker`.
   - Wrap the `Gtk.Picture` directly as the child of the card `Gtk.Button` for a clean, distraction-free grid presentation.

### Rationale
- Satisfies FR-030 and SC-016. Ensures visual consistency across the application by reflecting the identical aspect ratio used in game grid tiles and the details view, while removing unnecessary and redundant textual clutter and preventing any border cut-offs in an expanded dialog window.

### Alternatives Considered
- **Using Gtk.ContentFit.COVER without padding**: Causes edge borders and corner details on SteamGridDB images to be sliced/clipped when their natural pixel aspect ratio differs slightly from 2:3. `CONTAIN` within an exact 2:3 frame ensures every border pixel is visible without distortion.
- **Maintaining badge/pill overlays for animated covers**: Rejected per explicit user instruction to eliminate all labels, including "Animated".

---

## 10. Cover Overlay Loading Spinner During SteamGridDB Staging

### Decision
1. **Centered Adw.Spinner in Cover Overlay**:
   - In `cartridges/ui/game-details.blp`, inside the cover `Overlay`, add an `[overlay]` child `Adw.Spinner cover_spinner` configured with `halign: center; valign: center;` to center it horizontally and vertically over the game cover widget.
   - Bind `visible` to `template.cover-loading` (or `template.cover-spinner-visible`).
2. **State Management in GameDetails**:
   - Add a GObject property `cover_loading = GObject.Property(type=bool, default=False)` to `GameDetails`.
   - Set `self.cover_loading = True` when SteamGridDB download begins in `_stage_sgdb_cover(url)`.
   - Clear `self.cover_loading = False` in `apply_staging()` on UI thread, or in error handlers (`HTTPError`, `URLError`, `TimeoutError`, `OSError`, `ValueError`).
   - Also reset `cover_loading = False` in `_reset_cover_staging()`, `_cancel()`, and `_apply()`.
3. **Visual Styling**:
   - Give the spinner a suitable size (e.g. 36px or 48px) and style class or semi-transparent backdrop if needed, guaranteeing high visibility and immediate feedback to the user while network requests and PIL image processing execute.

### Rationale
- Satisfies FR-031 and SC-017. Provides immediate user feedback during asynchronous SteamGridDB downloading and resizing, avoiding user confusion about perceived UI freezes.

### Alternatives Considered
- **Disabling entire dialog**: Too restrictive and prevents cancelling or navigating while an image downloads.
- **Toast notification**: Ephemeral and disconnected from the cover widget; in-place spinner directly informs the user where the pending change will take effect.
