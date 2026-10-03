# Research & Technical Decisions: SteamGridDB Cover Picker and Credentials UX

**Feature**: SteamGridDB Cover Picker and Credentials UX
**Branch**: `004-steamgriddb-picker`
**Date**: 2026-10-03

## Codebase Status & Implementation Review

An architectural review of the existing codebase reveals that several components of this feature are already built and verified:

| User Story / Requirement | Code Location | Status | Notes |
|--------------------------|---------------|--------|-------|
| **US1**: API key masking & eye icon | `cartridges/ui/preferences.blp`, `preferences.py` | To Do | Currently uses `Adw.EntryRow`. Needs migration to `Adw.PasswordEntryRow`. |
| **US2 (part a)**: Dialog sizing (>= 760x520) | `cartridges/ui/cover_picker.blp` | Done | Configured to 800x580 (`content-width: 800; content-height: 580;`). |
| **US2 (part b)**: 2:3 aspect ratio, no clipping | `cartridges/ui/cover_picker.py` | Done | Thumbnail picture sized to 140x210 with `CONTAIN` fit and no text overlays. |
| **US2 (part c)**: Initial centered loading spinner & empty page | `cartridges/ui/cover_picker.blp`, `cover_picker.py` | To Do | Needs `Gtk.Stack` with `loading` (`Adw.Spinner`), `empty` (`Adw.StatusPage`), and `results`. |
| **US3**: Bottom centered spinner for progressive batches | `cartridges/ui/cover_picker.blp`, `cover_picker.py` | To Do | Needs vertical `Gtk.Box` holding `flowbox` and centered `bottom_spinner`. |
| **US4**: Thumbnail caching & lifecycle cleanup | `cartridges/utils/steamgriddb.py`, `application.py` | To Do | Needs XDG cache storage (`~/.cache/cartridges/previews/`), hashing, TTL pruning, and shutdown cleanup. |
| **US5**: Title prerequisite & error styling | `cartridges/ui/game_details.py` | Done | Lines 273-277 validate non-empty title, add `error` class to `name_entry`, and focus entry. |
| **US6**: Cover selection & staging feedback spinner | `cartridges/ui/game_details.py` | Done | Lines 328-372 use `self.cover_loading` GObject property with centered spinner overlay during async download. |

---

## 1. Credentials Visibility Toggle (Eye Icon)

### Context & Need
In the application preferences under the SteamGridDB section, the API key entry currently exposes the plaintext key directly in an `Adw.EntryRow`. The requirement is to mask the API key by default to protect sensitive credentials from shoulder surfing, and provide an eye icon toggle button that switches between masked and revealed plaintext.

### Decision
Replace `Adw.EntryRow` with `Adw.PasswordEntryRow` for the `sgdb_key_entry_row` element in `cartridges/ui/preferences.blp` and `cartridges/ui/preferences.py`.

### Rationale
- `Adw.PasswordEntryRow` is the official GNOME / Libadwaita standard component for secret and token input.
- It provides built-in, native masking of text characters out of the box.
- It includes a built-in eye icon button that toggles between obscured glyphs and plaintext visibility according to GNOME desktop conventions.
- It subclasses `Adw.EntryRow`, retaining identical GObject properties (`text`, `title`, signals such as `changed`), avoiding complex custom icon or reveal button code.
- Fully supported by `blueprint-compiler` in the `gtk-dev` container.

### Alternatives Considered
- *Custom `Adw.ActionRow` with a `Gtk.PasswordEntry` child*: Unnecessary boilerplate and inconsistent row padding compared to native `Adw.PasswordEntryRow`.
- *Custom suffix button in `Adw.EntryRow`*: Reinventing the wheel; lacks native accessibility integration provided by `Adw.PasswordEntryRow`.

---

## 2. Initial Cover Search Loading Indicator

### Context & Need
When opening the SteamGridDB cover art chooser dialog (`CoverPicker`), the dialog initially displays an empty window while the autocomplete search and initial grid requests are executed in the background. The user requires an active centered spinner while the initial batch of candidate images is being queried and loaded.

### Decision
Wrap the dialog body in a `Gtk.Stack` containing three states:
1. `loading`: Displays an `Adw.Spinner` centered both horizontally and vertically (`halign: center`, `valign: center`, dimension 48x48).
2. `empty`: Displays an `Adw.StatusPage` with icon `image-missing-symbolic` and a descriptive message when no results are found or if an error occurs.
3. `results`: Displays the `ScrolledWindow` containing the candidate grid `FlowBox`.

When `CoverPicker` initializes, the stack shows `loading`. When the first batch of candidate images is ready and added to the flowbox, the stack transitions cleanly to `results`. If zero candidates are found or an error occurs, the stack switches to `empty`.

### Rationale
- `Gtk.Stack` provides clean state separation and prevents layout shifting or partial empty views.
- `Adw.Spinner` is the modern Libadwaita progress spinner component conforming to GNOME HIG.
- An empty state status page prevents an ambiguous blank dialog when games have no matching grids on SteamGridDB.

### Alternatives Considered
- *Overlaying an `Adw.Spinner` on top of `FlowBox`*: Can cause clipping or interaction confusion if mouse events pass through to an empty grid.
- *Displaying spinner in headerbar*: Too subtle; users expect primary visual feedback in the dialog canvas for modal chooser queries.

---

## 3. Centered Bottom Spinner for Progressive Batch Loading

### Context & Need
SteamGridDB queries can return dozens of grid options. Loading all full or thumbnail images at once introduces latency and memory spikes. When displaying initial candidates, additional candidates should load progressively, with a loading spinner horizontally centered at the bottom of the list indicating ongoing background retrieval.

### Decision
1. Inside the `ScrolledWindow`, structure the child as a vertical `Gtk.Box` containing:
   - `FlowBox flowbox` (top child, displaying loaded cover buttons)
   - `Adw.Spinner bottom_spinner` (bottom child with `halign: center; valign: center; margin-bottom: 24; margin-top: 8; width-request: 32; height-request: 32;`)
2. Initial batch (first 6 to 8 candidates) is loaded while the initial centered spinner is visible. Once the initial batch is rendered, the view switches to `results`.
3. If additional candidates remain in the query results, `bottom_spinner` is set to visible and active. Subsequent batches are downloaded asynchronously.
4. As each subsequent preview is ready, it is appended to `flowbox`.
5. When all candidates are loaded or when the search query completes, `bottom_spinner` is hidden (`visible = False`).

### Rationale
- Placing `bottom_spinner` in the vertical box beneath `flowbox` within the `ScrolledWindow` ensures it naturally sits below current items and scrolls with the list.
- Explicit `halign: center` guarantees horizontal centering across all window widths and column configurations.
- Dynamic visibility ensures the spinner is only displayed when background fetching is actively underway.

### Alternatives Considered
- *FlowBox child widget*: A child inside `Gtk.FlowBox` occupies a grid cell and aligns to the grid columns rather than centering across the whole container width.
- *Fixed bottom overlay*: Can obscure the bottom row of candidate covers. Placing it inside the scrolling box provides a natural, non-overlapping document flow.

---

## 4. Cover Thumbnail Caching and Lifecycle Cleanup

### Context & Need
Preview thumbnails downloaded from SteamGridDB should be cached locally so reopening the cover chooser does not trigger redundant network requests. The cache must be purged on application exit or evicted when entries expire, ensuring zero unbounded disk growth.

### Decision
1. **Cache Location**: Store preview files in `GLib.get_user_cache_dir() / "cartridges" / "previews"`, conforming to standard XDG cache directory layout and project Constitution Principle V (Resource and Asset Sandboxing).
2. **Cache Key & Storage**:
   - Cache keys are generated by hashing the source image URL with SHA-256 (`hashlib.sha256(url.encode("utf-8")).hexdigest()`).
   - Cached files are saved as raw image bytes (PNG/JPG/WEBP/GIF) with file extension matching image format or `.bin`.
   - File modification time (`mtime`) records cache entry timestamp.
3. **Cache Invalidation & Expiration**:
   - Expiration TTL: Default to 7 days (`7 * 86400` seconds).
   - When retrieving an image, if cached file exists and `(now - mtime) < TTL`, cached data is read directly from disk.
   - On application startup or cache initialization, an asynchronous scan prunes files older than TTL.
4. **Clear on Exit**:
   - Connect to `Application.do_shutdown` lifecycle hook in `cartridges/application.py`.
   - On shutdown, delete temporary preview cache files to honor session clearance.

### Rationale
- Using `$XDG_CACHE_HOME` ensures temporary preview files are separated from permanent game covers stored in `$XDG_DATA_HOME/cartridges/covers`.
- SHA-256 URL hashing prevents filename collisions and illegal path characters.
- Combining TTL expiration pruning with shutdown cleanup guarantees bounded disk utilization.

### Alternatives Considered
- *In-memory only cache*: Discarded on dialog close, causing redundant network traffic whenever user reopens chooser during session.
- *Storing previews in `COVERS_DIR` (`$XDG_DATA_HOME`)*: Violates XDG conventions by mixing temporary unselected candidate previews with permanent library artwork.
