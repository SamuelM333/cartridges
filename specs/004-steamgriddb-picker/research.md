# Research & Technical Decisions: SteamGridDB Cover Picker and Credentials UX

**Feature**: SteamGridDB Cover Picker and Credentials UX
**Branch**: `feat/004-sgdb-sticky-search`
**Date**: 2026-10-06

## Codebase Status & Implementation Review

An architectural review of the existing codebase confirms that US1 through US6 are completed and merged into main. The current scope centers on US7:

| User Story / Requirement | Code Location | Status | Notes |
|--------------------------|---------------|--------|-------|
| **US1**: API key masking & eye icon | `cartridges/ui/preferences.blp`, `preferences.py` | Done | Implemented via `Adw.PasswordEntryRow`. |
| **US2 (part a)**: Dialog sizing (>= 760x520) | `cartridges/ui/cover_picker.blp` | Done | Configured to 800x580 (`content-width: 800; content-height: 580;`). |
| **US2 (part b)**: 2:3 aspect ratio, no clipping | `cartridges/ui/cover_picker.py` | Done | Thumbnail picture sized to 140x210 with `CONTAIN` fit and no text overlays. |
| **US2 (part c)**: Initial centered loading spinner & empty page | `cartridges/ui/cover_picker.blp`, `cover_picker.py` | Done | Implemented via `Gtk.Stack` with `loading`, `empty`, and `results`. |
| **US3**: Bottom centered spinner for progressive batches | `cartridges/ui/cover_picker.blp`, `cover_picker.py` | Done | Implemented via vertical `Gtk.Box` holding `flowbox` and centered `bottom_spinner`. |
| **US4**: Thumbnail caching & lifecycle cleanup | `cartridges/utils/steamgriddb.py`, `application.py` | Done | Implemented in `$XDG_CACHE_HOME/cartridges/previews/` with TTL and exit cleanup. |
| **US5**: Title prerequisite & error styling | `cartridges/ui/game_details.py` | Done | Validates non-empty title, adds `error` class to `name_entry`, and focuses entry. |
| **US6**: Cover selection & staging feedback spinner | `cartridges/ui/game_details.py` | Done | Centered spinner overlay during async download in Game Details. |
| **US7**: Sticky search bar in cover chooser | `cartridges/ui/cover_picker.blp`, `cover_picker.py` | To Do | Persistent `SearchEntry` in `Adw.ToolbarView` `[top]`, pre-populated with initial query, re-searching on activate. |


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

---

## 5. Fixed Mask Length for Stored API Key

### Context & Need
By default, `Adw.PasswordEntryRow` renders one masked bullet character (`•`) for every character in the stored string. A standard SteamGridDB API key is 32 hexadecimal characters long. Rendering 32 dots reveals the exact length of the user's secret key and can cause horizontal scrolling or awkward layout inside the preferences row. The user wants the field to display a set amount of masked characters that comfortably fits the input field instead of matching the real string length.

### Decision
1. In `CartridgesPreferences`, maintain an internal string variable `self._real_sgdb_key` loaded from `SETTINGS.get_string("sgdb-key")`.
2. Define `FIXED_MASK_CHARS = "•" * 20` (or 20 bullet dots) representing a populated, masked state.
3. When the entry row is unfocused and masked:
   - If `self._real_sgdb_key` is empty, set entry row text to `""`.
   - If `self._real_sgdb_key` is populated, set entry row text to `FIXED_MASK_CHARS`.
4. When the user toggles the eye reveal button or focuses the entry row to edit:
   - Temporarily substitute `self._real_sgdb_key` into the entry row so the user views or edits their actual key.
5. When the user finishes editing and focus is lost or reveal is toggled off:
   - Save the edited text to `self._real_sgdb_key` and update `SETTINGS["sgdb-key"]`.
   - Re-apply `FIXED_MASK_CHARS` if currently masked.

### Rationale
- Completely conceals both the contents and the exact length of the API key from observers.
- Prevents text overflow or clipping within the entry row container.
- Matches standard security practices seen in password managers and web console secret fields.

### Alternatives Considered
- *Native `Adw.PasswordEntryRow` length mapping*: No native property exists in Libadwaita to decouple mask bullet count from text buffer length without managing virtual display text.
- *Placeholder text only*: Using placeholder text leaves the field looking empty rather than securely configured.

---

## 6. Focus Loss on Clicking Away

### Context & Need
In GTK 4, clicking on background containers, preferences group headers, or empty window regions does not inherently take keyboard focus away from an active `Gtk.Text` or `Adw.PasswordEntryRow`. Users expect that clicking away from the API key input row immediately releases focus, signaling that input is complete and triggering mask restoration.

### Decision
1. Attach a `Gtk.GestureClick` controller to the preferences view/page. In its release/press handler, if focus is currently within `sgdb_key_entry_row`, invoke `self.set_focus(None)` (or `root.set_focus(None)`).
2. Attach an `EventControllerKey` to `sgdb_key_entry_row` to capture `Return`/`Enter` and `Escape`, clearing focus upon confirmation or cancellation.
3. Attach a `Gtk.EventControllerFocus` to `sgdb_key_entry_row` to detect focus in and focus out events cleanly:
   - `focus-enter`: Prepare field for editing (load real key if masked).
   - `focus-leave`: Commit changes to GSettings, refresh sensitivity, and apply the fixed mask.

### Rationale
- Intuitive and responsive desktop UX matching standard desktop behavior.
- Cleanly triggers the focus-out lifecycle needed to swap between editing text and the fixed display mask.
- Non-disruptive: only clears focus if no other focusable widget was clicked.

### Alternatives Considered
- *Requiring explicit Enter key press only*: Inconvenient for mouse-driven users who expect clicking outside to commit and blur the field.
- *Window-level global modal focus grabbing*: Too aggressive; can break tab navigation or interaction with other preference controls.

---

## 7. Sticky Search Bar in Cover Chooser

### Context & Need
When browsing SteamGridDB for covers, the initial search term queried is the game title saved in Cartridges. However, titles often contain extra edition tags (e.g., "Game of the Year Edition"), regional variances, or typos that yield suboptimal or empty results from SteamGridDB. Users need a persistent search bar in the cover picker dialog that:
1. Is sticky at the top so it remains accessible even while scrolling through dozens of results.
2. Is pre-populated with the queried search term so users know what was queried.
3. Allows editing the search term and pressing Enter to re-query SteamGridDB without leaving the dialog or having to cancel and rename the game.

### Decision
1. **Widget Architecture in Blueprint**:
   - In `cartridges/ui/cover_picker.blp`, inside `Adw.ToolbarView`, add a second `[top]` child beneath `Adw.HeaderBar`:
     ```blueprint
     [top]
     Adw.Clamp {
       maximum-size: 500;
       margin-top: 6;
       margin-bottom: 10;
       margin-start: 16;
       margin-end: 16;

       child: SearchEntry search_entry {
         placeholder-text: _("Search SteamGridDB…");
         activate => $_on_search_activated();
         search-changed => $_on_search_changed();
       };
     }
     ```
   - Placing the clamp and `SearchEntry` within the `[top]` slot of `Adw.ToolbarView` guarantees that the search entry stays fixed ("sticky") above the dialog's scrollable `content: Stack stack`, with zero vertical displacement during scrolling.
2. **Pre-population**:
   - In `CoverPicker.__init__`, initialize `self.search_entry.set_text(self.game_name)`.
   - The user immediately sees the initial title searched for.
3. **Re-searching & Asynchronous Cancellation**:
   - When the user presses Enter (`activate` signal), extract the query string via `self.search_entry.get_text().strip()`.
   - If the query is empty or whitespace-only, do not send an empty query.
   - Maintain a search generation counter (`self._search_generation: int = 0`). Increment `self._search_generation` on each new search.
   - Any background task from an earlier generation checking `if generation != self._search_generation:` aborts cleanly without rendering stale results.
   - Cancel any existing `self._fetch_task` if still running.
   - Clear existing `flowbox` items, set `self.stack.set_visible_child_name("loading")`, reset `bottom_spinner`, and launch `_fetch_covers()` with the new query.
4. **State Persistence Across Stack Transitions**:
   - Because the search bar is located in `Adw.ToolbarView [top]` outside `Gtk.Stack`, it remains visible, interactive, and pre-populated across all stack states (`loading`, `results`, and `empty`).
   - If a search yields `empty` ("No Covers Found"), the user can immediately refine the query in the search bar without having to dismiss or reopen the dialog.

### Rationale
- Strictly follows GNOME HIG and Libadwaita layout patterns by utilizing `Adw.ToolbarView` top bars.
- `Adw.Clamp` ensures consistent max width across varied screen sizes and window scaling.
- Explicit activation (Enter key) avoids spamming SteamGridDB API on every keystroke, which would quickly exhaust rate limits and cause UI jank.
- Generation counter ensures race conditions between overlapping network queries are safely eliminated.

### Alternatives Considered
- *Search Entry inside HeaderBar title widget*: Cluttered; reduces title readability and restricts search bar width in an 800px modal dialog.
- *Search Entry inside ScrolledWindow / Flowbox*: Scrolls off-screen when browsing results, violating the requirement for a persistent, sticky search bar.
- *Auto-search on keystroke (search-changed) with debounce*: While viable, auto-querying an external authenticated REST API with rate limits can easily cause unwanted network traffic for incomplete words. Explicit activation matches standard desktop chooser patterns.
