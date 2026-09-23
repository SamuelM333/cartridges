# Quickstart Validation Guide: Preferences Dialog, Flatpak, and SteamGridDB

This guide outlines manual and automated validation scenarios required to build, run, and test the preferences dialog, modular Flatpak scanning, and SteamGridDB integration.

## 1. Prerequisites

Ensure the following tools are installed on your system or inside your development environment:
- Python 3.13+ (Python 3.14 in container)
- Meson (>= 1.1.0) and Ninja
- glib-compile-schemas (for GSettings validation)
- blueprint-compiler (>= 0.22.0)
- flatpak-builder or flatpak CLI (for Flatpak source validation)

---

## 2. Build and Schema Verification

Run the following commands to configure and compile the build environment to ensure GSettings schemas contain all required preferences keys:

```bash
# Clean up any prior build directory
rm -rf _build

# Setup and configure the build directory
meson setup _build

# Compile schemas and assets
meson compile -C _build
```

### Expected Outcome
The build must succeed with zero compiler or validation errors. Schema compilation will fail with clear errors if any of the GSettings preference keys (such as `exit-after-launch` or `sgdb-key`) are missing or have mismatched types.

---

## 3. Manual Verification Scenarios

All UI layouts and functionality must be verified by launching the application.

```bash
# Launch the application in development mode
python3 -m cartridges
```

### Scenario A: Preferences Dialog and Design Parity
1. Launch the application.
2. Click the open-menu button in the upper-right corner and select **Preferences**.
3. Verify that:
   - The Libadwaita preferences dialog opens immediately (under 200ms).
   - Three pages are displayed: **General**, **Import**, and **SteamGridDB**, matching the exact visual structure, groups, and titles from the legacy `main` branch.
   - No custom styling, non-standard layouts, or new UI elements are present (as per FR-022 and A-007).

### Scenario B: GSettings Property Binding
1. Open **Preferences** and go to **General**.
2. Toggle the **Exit After Launching Games** switch.
3. In a separate terminal, run:
   ```bash
   gsettings get page.samuelm333.Cartridges exit-after-launch
   ```
4. Verify that the output is `true`. Toggle it off and verify it returns to `false`.
5. Repeat for other toggles (e.g. "Cover Image Launches Game", "High Quality Images", "Use SteamGridDB") to ensure instant bidirectional persistence.

### Scenario C: Danger Zone Data Removal and Undo Safety
1. Ensure several games are present in your grid library.
2. Open **Preferences**, scroll to the bottom of **General**, and click **Remove All Games**.
3. Confirm the action in the prompt.
4. Verify that:
   - All games are removed from the grid immediately.
   - An in-app Toast notification appears at the bottom saying "All games removed" with an **Undo** button.
5. Click **Undo** (or press `<Ctrl>+z` inside the preferences screen).
6. Verify that all games are successfully restored to the library.

### Scenario D: Flatpak Source Importing
1. Ensure at least one Flatpak game is installed on your host system.
2. Open **Preferences**, go to the **Import** tab, and expand the **Flatpak** expander row.
3. Turn on the source switch.
4. Verify that the system path `/var/lib/flatpak` and user path `~/.local/share/flatpak` are resolved. If they are not found, verify a warning indicator is shown on the row.
5. Close Preferences and trigger a library import scan.
6. Verify that the Flatpak game is successfully detected, added to the grid with its desktop icon/cover, and can be launched correctly.

### Scenario E: SteamGridDB Cover Art Retrieval, Real-Time Progress, and Auto-Fetch
1. Open **Preferences** and select the **SteamGridDB** tab.
2. With an invalid or blank key, verify that clicking "Update" displays an alert toast informing the user to configure a valid API key, terminating immediately without crashing.
3. Paste a valid SteamGridDB API key in the **API Key** text entry field.
4. Verify that the **Use SteamGridDB** toggle becomes sensitive/unlocked once a key is entered, and locks again if the key is deleted.
5. Toggle **Use SteamGridDB** on, then click **Update Covers**.
6. Verify that:
   - A dedicated progress row appears under "Update Covers" displaying `Updating: <Game Name>` and progress fraction `<Index>/<Total> games`.
   - The `ProgressBar` fraction smoothly fills up as each game is scanned.
   - The application remains completely responsive and clickable at a smooth 60 FPS while downloading images.
   - Detailed INFO and WARNING logs appear in GNOME Builder execution console.
   - On completion, the progress row hides, the dismissable status message appears in the section (e.g., `Finished updating covers: X/Y successful.`), and covers refresh in the main grid.
   - Click the dismiss button on the status message and verify it closes cleanly.
7. Restart the application with `sgdb` enabled and observe that missing covers for uncovered games are automatically fetched in the background without user intervention.

### Scenario F: Legacy Cover Overlay Buttons in Game Edit Page with Staged Commit & Reversibility
1. In the main grid, select any game to open its details view.
2. Confirm that no cover action buttons (folder, globe, trash) are present on the cover in the standard game details view.
3. Click the **Edit** action button in the action bar to enter the Edit Game view.
4. Verify that the legacy cover action buttons appear directly over the cover:
   - A folder button (`folder-symbolic`) with tooltip "Browse files" to choose a local image file.
   - A globe button (`globe-symbolic`) with tooltip "Browse SteamGridDB" to search and pick from SteamGridDB.
   - A trash can button (`user-trash-symbolic`) to remove the cover (visible when a cover is set).
5. Click the folder button, pick a local image file:
   - Verify the cover preview updates immediately in the edit pane.
6. Click **Cancel**:
   - Verify that edit mode exits and the game's original cover remains completely untouched on disk and on the view (action reversed).
7. Click **Edit** again, click the globe button, and select a cover from the SteamGridDB picker (capped at 10 items):
   - Verify the cover preview updates.
8. Click the trash can button:
   - Verify the cover clears (reverting to placeholder) and the trash button is hidden.
9. Click **Apply**:
   - Verify that the staged cover modification is committed to disk (updating or removing the cover file in `COVERS_DIR`) and updated on the game.

### Scenario G: Title Validation and Adding New Game with Cover
1. In the main window, click the **Add Game** button to open the Add Game view (`game is None`).
2. Verify that:
   - The folder button (`folder-symbolic`) is active and clickable immediately.
   - Selecting a local image stages the cover and previews it in the view.
3. With the **Title** field empty, click the SteamGridDB globe button:
   - Verify that the cover picker does not open.
   - The Title entry gets an error visual indicator (`error` CSS class with red styling) and receives focus.
4. Type a game title into the Title field:
   - Verify that the error indicator immediately clears.
5. Click the SteamGridDB globe button:
   - Verify that SteamGridDB search opens using the entered title text and displays cover results.
6. Select a cover, populate the executable field, and click **Add**:
    - Verify that the new game is created and the staged cover image is saved to disk and associated with the new game.

### Scenario H: SteamGridDB Cover Candidate Dialog Sizing, Aspect Ratio, and Clean Visuals
1. In the Edit Game or Add Game view, enter a valid game title and click the SteamGridDB globe button.
2. Observe the candidate cover options displayed in the dialog:
   - The dialog is sized generously relative to the main window (content size 800x580).
   - Each cover card preview renders in the exact 2:3 aspect ratio (140x210 or 160x240) matching game details cover proportions.
   - The entire image and its complete perimeter/borders are fully visible without being cropped or having borders cut off.
   - Zero text labels (neither "Static" nor "Animated") are rendered below or on top of any cover card.
3. Click any cover card to select it and confirm that the preview updates accurately in the Edit view.

### Scenario I: SteamGridDB Cover Loading Spinner
1. In the Edit Game or Add Game view, select a cover from the SteamGridDB cover picker dialog.
2. Observe the cover area in the Edit Game pane immediately upon selection:
   - A loading spinner appears centered vertically and horizontally over the game cover widget.
   - The user cannot see broken or half-loaded assets while the background download occurs.
3. Once download and local processing finish:
   - The loading spinner disappears.
   - The staged cover is displayed in the cover widget.
