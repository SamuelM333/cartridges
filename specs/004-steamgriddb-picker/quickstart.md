# Quickstart & Verification Guide: SteamGridDB Cover Picker and Credentials UX

**Feature**: SteamGridDB Cover Picker and Credentials UX
**Branch**: `004-steamgriddb-picker`
**Date**: 2026-10-03

## 1. Prerequisites & Environment

All compilation and validation commands must be executed within the `gtk-dev` Distrobox container per Constitution guidelines:

```bash
distrobox enter gtk-dev
```

Ensure build directory is configured:

```bash
meson setup _build --prefix=/usr
ninja -C _build
```

---

## 2. Automated Quality Gates

Verify code style, typing, and template compilation:

```bash
# Pre-commit checks
pre-commit run --all-files

# Blueprint compilation
blueprint-compiler compile cartridges/ui/cover_picker.blp
blueprint-compiler compile cartridges/ui/preferences.blp

# Static typing and linting
pyright
ruff check
```

---

## 3. Manual Scenario Verification

### Scenario 1: API Key Masking, Fixed Length & Focus Loss
1. Launch Cartridges:
   ```bash
   ninja -C _build run
   ```
2. Open Preferences via menu or `Ctrl+,` and select the **SteamGridDB** page.
3. Observe the **API Key** row under **Authentication**:
   - **Expected**: Any configured key appears masked with a fixed set amount of characters (e.g., 20 dots) that fits the field neatly, rather than displaying one dot per character of the real string.
4. Click on the API key row to focus it, or click away elsewhere in the preferences dialog:
   - **Expected**: Clicking away immediately releases focus from the API key row and commits any changes.
5. Click the eye icon toggle button on the right edge of the row:
   - **Expected**: The actual plaintext characters of the API key become visible.
6. Click the eye icon again:
   - **Expected**: The field returns to the fixed set amount of masked characters.

---

### Scenario 2: Initial Loading Spinner in Cover Picker *(To Do)*
1. In the main Cartridges window, click on any game with a valid title to open Game Details.
2. Click the edit button, then click the **Browse SteamGridDB** globe button.
   - **Expected**: The cover picker dialog opens immediately displaying a prominent loading spinner centered in the window.
3. Wait for the initial candidate images to arrive.
   - **Expected**: Once the first batch of candidate covers renders, the initial centered spinner is cleanly dismissed and the candidate grid is shown.

---

### Scenario 3: Bottom Centered Spinner for Progressive Batches *(To Do)*
1. In the open cover picker dialog, scroll down toward the bottom of the candidate list.
   - **Expected**: While additional candidate images are being fetched, a loading spinner is visible and horizontally centered below the grid.
2. Once all candidate covers for the query have loaded:
   - **Expected**: The bottom spinner automatically disappears.

---

### Scenario 4: Thumbnail Caching & Cleanup *(To Do)*
1. Open the cover picker for a game to load candidate thumbnails.
2. Verify cache storage on the host:
   ```bash
   ls -la ~/.cache/cartridges/previews/
   ```
   - **Expected**: SHA-256 hashed files exist corresponding to downloaded preview images.
3. Close and reopen the cover picker for the same game.
   - **Expected**: Candidate thumbnails appear instantly from local cache without network delay.
4. Close Cartridges:
   - **Expected**: Temporary preview cache files are cleanly removed or marked for expiration, leaving no orphaned disk bloat.

---

### Scenario 5: Title Validation Error Styling *(Done)*
1. Open Add Game or enter Edit mode on an existing game.
2. Clear the Title field so it is completely empty.
3. Click the globe button ("Browse SteamGridDB").
   - **Expected**: The Title entry immediately receives red error styling, gains focus, and the cover picker dialog is NOT opened.
4. Type any character into the Title entry.
   - **Expected**: The red error styling clears immediately.

---

### Scenario 6: Cover Selection Staging Spinner *(Done)*
1. Select a candidate cover from the SteamGridDB cover picker dialog.
2. Observe the cover area in Game Details.
   - **Expected**: An active loading spinner is centered horizontally and vertically over the cover preview while downloading and processing.
3. Once download and processing completes:
   - **Expected**: The spinner hides and the newly staged cover preview is displayed.
