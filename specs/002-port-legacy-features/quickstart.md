# Quickstart Validation Guide: Preferences Dialog, Flatpak, and SteamGridDB

This guide outlines the manual and automated validation scenarios required to build, run, and test the preferences dialog, modular Flatpak scanning, and SteamGridDB integration.

## 1. Prerequisites

Ensure the following tools are installed on your system or inside your development environment:
- Python 3
- Meson (>= 1.1.0) and Ninja
- glib-compile-schemas (for GSettings validation)
- flatpak-builder or flatpak CLI (for Flatpak source validation)

---

## 2. Build and Schema Verification

Run the following commands to configure and compile the build environment to ensure GSettings schemas contain all the required preferences keys:

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
1. Ensure at least one Flatpak game (e.g. SuperTuxKart or any game/app) is installed on your host system.
2. Open **Preferences**, go to the **Import** tab, and expand the **Flatpak** expander row.
3. Turn on the source switch.
4. Verify that the system path `/var/lib/flatpak` and user path `~/.local/share/flatpak` are resolved. If they are not found, verify a warning indicator is shown on the row.
5. Close Preferences and trigger a library import scan.
6. Verify that the Flatpak game is successfully detected, added to the grid with its desktop icon/cover, and can be launched correctly.

### Scenario E: SteamGridDB Cover Art Retrieval and Async Update
1. Open **Preferences** and select the **SteamGridDB** tab.
2. Paste a valid SteamGridDB API key in the **API Key** text entry field.
3. Verify that the **Use SteamGridDB** toggle becomes sensitive/unlocked once a key is entered, and locks again if the key is deleted.
4. Toggle **Use SteamGridDB** on, then click **Update Covers**.
5. Verify that:
   - An active progress spinner replaces the update button label.
   - A non-blocking toast notification saying "Downloading covers..." is displayed.
   - The application remains completely responsive and clickable at a smooth 60 FPS while downloading images.
   - On completion, the toast updates to "Covers updated" and game covers refresh in the main grid.

