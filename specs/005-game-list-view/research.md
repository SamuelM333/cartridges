# Technical Research: Main Game List View and Cover Interactions

**Branch**: `feat/005-game-list-view`
**Feature**: `specs/005-game-list-view`
**Date**: 2026-10-06

## 1. Hover Action Buttons Layout and Transition

### Problem Statement
In `cartridges-main`, hovering over a game card revealed two circular floating buttons at the top of the cover: a top-left action button (play/info) and a top-right contextual menu button ("three dots"). In the current codebase, the primary action button was temporarily replaced with a centered pill button at the bottom of the card. We need to restore the original, proven hover button design while integrating with the current Blueprint architecture.

### Research & Decisions
- **Decision**: Position two circular overlay buttons at the top corners of the cover overlay in `cartridges/ui/game-item.blp`:
  - Top-left (`halign: start`, `valign: start`, `margin-top: 6`, `margin-start: 6`): Action button (Play / Info).
  - Top-right (`halign: end`, `valign: start`, `margin-top: 6`, `margin-end: 6`): MenuButton with `view-more-symbolic` icon.
- **Rationale**: Restores visual harmony and unifies the top bar of the cover image. Placing buttons at the top prevents obscuring the bottom half of vertical artwork and maintains consistency with GNOME card patterns.
- **Alternatives Considered**:
  - *Bottom pill button (current)*: Rejected because it obscures the bottom center of the artwork, creates a heavier visual footprint, and diverges from the user-requested `cartridges-main` design.
  - *Revealer widgets vs. CSS transition*: In `cartridges-main`, `Gtk.Revealer` widgets with `crossfade` were used inside the overlay. In the current rewrite, CSS transitions (`opacity` and `transform`) via the `.hidden` style class are utilized on `#game-item overlay > button` and `#game-item overlay > menubutton > button`. Both achieve smooth fading without extra widget nesting; keeping the CSS transition pattern or aligning with revealer child properties maintains responsiveness and high performance.

## 2. Dynamic Action and Icon Swapping ("Cover image launches game")

### Problem Statement
When the user toggles "Cover Image Launches Game" in Preferences (`cover-launches-game` GSettings key), the behavior of clicking the cover and clicking the hover action button must invert immediately without needing an app restart:
- When disabled (default): Cover click opens details; hover button displays Play icon (`media-playback-start-symbolic`) and launches the game.
- When enabled: Cover click launches game; hover button displays Info icon (`help-about-symbolic`) and opens game details.

### Research & Decisions
- **Decision**: Update `GameItem._update_action_button` in `cartridges/ui/game_item.py`:
  - When `cover-launches-game` is true:
    - Button icon: `help-about-symbolic`
    - Button tooltip: `_("Details")`
    - Button action name: `game.details`
  - When `cover-launches-game` is false:
    - Button icon: `media-playback-start-symbolic`
    - Button tooltip: `_("Play")`
    - Button action name: `game.play`
- **Cover Click Binding**: Already implemented in `Window._show_details` in `cartridges/ui/window.py` where `single-click-activate` on the `GridView` checks `SETTINGS.get_boolean("cover-launches-game")` and either invokes `game.play()` or navigates to details.
- **Alternatives Considered**:
  - *Hardcoding two separate button widgets in the template and toggling visibility*: Rejected as unnecessary duplication; changing the icon, tooltip, and action-name on a single button widget is cleaner, less memory-intensive, and eliminates widget sync bugs.

## 3. Popover Menu Persistence on Hover Exit

### Problem Statement
When the user clicks the three-dots menu button, the pointer might drift outside the game item card boundaries while selecting a menu entry. The menu button must not disappear or collapse while its popover menu remains open.

### Research & Decisions
- **Decision**: Track `options.props.active` in `GameItem._reveal_buttons`.
  - The reveal condition for the menu button evaluates `contains_pointer or self.options.props.active`.
  - As long as `options.props.active` is true, the menu button remains visible and interactive.
- **Rationale**: Matches the implementation in `cartridges/ui/game_item.py` and `cartridges-main`, preventing sudden dismissal of controls during contextual interactions.

## 4. Accessibility, Focus Outlines, and Controller Navigation

### Problem Statement
Users navigating via keyboard or connected gamepads must be able to focus cards and trigger primary and secondary actions without requiring mouse hover.

### Research & Decisions
- **Decision**:
  - The `GridView` handles focus navigation across game cards with visible focus outlines (`focus-visible`).
  - Activating a focused item via keyboard (`Return` / `Space`) triggers `GridView` item activation, respecting `cover-launches-game`.
  - Contextual actions remain accessible via standard keyboard shortcuts (`Ctrl+N`, `Delete` for remove where applicable) and context menu keys (`Menu` key or `Shift+F10`).
  - Gamepad navigation leverages the existing `gamepads.py` monitor and directional navigation.

## 5. Dismissable Game Launch Toast Notification & Internationalization

### Problem Statement
When a game is launched from the UI, the user needs clear, non-intrusive feedback confirming that the launch command was dispatched, without blocking the interface. The notification must display the localized message "Launched <game name>" and support translation across diverse grammatical structures.

### Research & Decisions
- **Decision**:
  - Introduce a centralized `play(game: Game) -> None` function in `cartridges/ui/games.py`.
  - When invoked, it calls `game.play()` and dispatches an in-app toast via `_window().send_toast(_("Launched {}").format(game.name))`.
  - Provide an explicit translation comment `# Translators: {} is the name of the game that was launched` immediately before the gettext call so that GNU gettext extracts context for translators.
  - Update `GameActions` (`"play"` action entry) and `Window._show_details` (cover click when `cover-launches-game` is true) to call `games.play(game)`.
- **Rationale**:
  - `Window.send_toast` already integrates with `Adw.ToastOverlay` and creates an `Adw.Toast(title=title, use_markup=False)`.
  - In Libadwaita, `Adw.Toast` is dismissable by default (via user swipe/interaction or automatically fading after the system timeout).
  - Placing `play(game)` in `cartridges/ui/games.py` follows the established pattern of `hide(game)`, `unhide(game)`, and `remove(game)` in the same module.
  - Using `{}` placeholder formatting is consistent with existing localized toast strings in Cartridges (`_("{} hidden")`, `_("{} unhidden")`, `_("{} removed")`), allowing translators to position the game name at the beginning, middle, or end of the translated sentence.
- **Alternatives Considered**:
  - *Dispatching toast from domain model (`cartridges/games.py`)*: Rejected because domain model objects should not import UI widgets or window controllers, preserving clean architecture (Constitution Principle II).
  - *Displaying system desktop notifications via libnotify/portal*: Rejected as too disruptive for standard game launches where the main application window is already in focus.

## 6. Current State of "Last Played" (Amendment 2026-10-08)

### Problem Statement
The spec asks for "Last Played" sorting to use the exact time, and for a launched game to move to the first position. Before designing, we checked what the codebase already does.

### Findings
- `Game.last_played` (`cartridges/games.py`) is a `GObject.Property(type=int)` holding a Unix timestamp in seconds. The only source that sets it is Steam (`cartridges/sources/steam.py`, `LastPlayed` from the app manifest), which is already seconds-precise.
- `_sort` in `cartridges/ui/games.py` compares the full integer (`(a > b) - (a < b)`) under the `last_played` mode with `invert=True`, and ties fall back to `_name_cmp(game1.name, game2.name)`. Never-played games have `0` and therefore sort last. FR-016 and FR-017 are already satisfied by the comparator.
- `Game.play()` never sets `last_played`. Every Cartridges launch currently leaves the value untouched, so non-Steam games stay at `0` and tie alphabetically. This is the root cause of the user-visible problem.
- Nothing calls `sorter.changed(...)` after a launch, so even if `last_played` were set, the `Gtk.SortListModel` would not move the item (FR-018).
- Only `imported` games are written to disk (`Game.save()`, `GAMES_DIR/imported_*.json`). Games from launcher sources are rebuilt from the launcher on every start, so a value set in memory would be lost on restart (FR-015).
- `game_id` is always prefixed with its source ID (`steam_`, `lutris_`, `heroic_`, `imported_`, ...), so it is unique across sources and safe to use as a key.

### Decision
Do not change the sort comparator. Fix recording, persistence, merge, and re-sort (sections 7-9).

## 7. Persisting Cartridges-Recorded Launch Times

### Decision
Add a module `cartridges/play_history.py` that owns a single JSON object at `DATA_DIR / "last-played.json"` (`$XDG_DATA_HOME/cartridges/last-played.json`) mapping `game_id` (str) to a Unix timestamp in seconds (int).
- `load()` reads the file once and caches it. Missing file, unreadable file, invalid JSON, or entries that are not `str -> int` yield an empty mapping or are skipped; loading never raises (SC-009).
- `record(game_id, timestamp)` updates the cached mapping and writes the whole file atomically (write to a temporary file in the same directory, then `os.replace`), so a crash mid-write cannot corrupt existing history.
- The write is synchronous. It must complete before `exit-after-launch` calls `app.quit()` (FR-015), and the file is tiny (one entry per launched game).

### Rationale
- Works the same for every source without touching individual source modules (Principle II).
- Keeps launcher-derived game objects stateless, matching how they are rebuilt today.
- One small file is cheaper and simpler than one file per game.

### Alternatives Considered
- *Call `Game.save()` for every source*: Rejected. The loader only reads `imported_*.json`, so this would need a second, general merge path for every property of every source, which is a much larger change (it is effectively general per-game state persistence, out of scope here).
- *Store the map in GSettings (`a{sx}` in the State schema)*: Rejected. GSettings is meant for preferences and window state, not an unbounded per-game data set; it would also require a schema change and migration.
- *Widen `last_played` to a 64-bit property to avoid the year-2038 limit*: Deferred. `GObject.Property(type=int)` is 32-bit signed, which overflows in 2038 for every timestamp property (`added` too). It affects more than this feature and should be handled separately.

## 8. Recording the Launch Time and Merging with Launcher Data

### Decision
- In `Game.play()` (`cartridges/games.py`), before spawning the subprocess:
  1. `self.last_played = int(time.time())`
  2. `play_history.record(self.game_id, self.last_played)`
  3. Spawn the process, then honour `exit-after-launch` as today.
  Recording first means the time is saved even if the launch fails or the game exits immediately (spec edge case), and is saved before the application can quit.
- In `Source._get_games` (`cartridges/sources/__init__.py`), after `game.added` is filled in, set `game.last_played = max(game.last_played, play_history.load().get(game.game_id, 0))`. This satisfies FR-019 (keep the newer of launcher-reported and Cartridges-recorded) for all sources, including `imported`.
- If the system clock went backward, the new time may be older than an existing one; we still record what the clock reports (spec edge case, accepted).

### Rationale
- `Game.play()` is the single domain entry point for every launch path (hover Play, cover click, keyboard/gamepad activation, details view Play), so FR-014 is covered in one place.
- Doing the merge in the shared `Source` wrapper keeps the rule in one place and leaves source modules unaware of Cartridges history.

### Alternatives Considered
- *Record in `cartridges/ui/games.play()`*: Rejected. It would put persistence logic in the UI layer and miss any future launch path that calls `Game.play()` directly.
- *Always prefer the Cartridges-recorded time*: Rejected. It would hide newer plays started directly from Steam or another launcher (FR-019).

## 9. Re-sorting So the Launched Game Moves First

### Decision
In `cartridges/ui/games.play()`, after `game.play()` returns, call `sorter.changed(Gtk.SorterChange.DIFFERENT)`. This is the same pattern already used in `GameEditable.apply` when a name changes.
- Under "Last Played", the launched game now has the newest timestamp, so the `Gtk.SortListModel` moves it to position 0 of the full list and of any filtered view (search, collection, hidden), satisfying FR-018 without clearing the filter.
- Under any other sort mode, `last_played` is not part of the comparison, so the order does not change (FR-021). The call is still made unconditionally to keep the code simple; re-sorting a library of typical size is negligible.
- When launching from the details view, the list is re-sorted while the details page is shown, so the game is first on return (acceptance scenario 7).
- Launching the game that is already first produces no position change, so no visible reshuffle.

### Open Verification (not a blocker)
How `Gtk.GridView` handles scroll position and keyboard focus when the focused item moves from position N to 0 is a GTK toolkit behaviour. The spec requires that the grid does not force-scroll to the top and that focus is not moved to an unrelated card. This is verified manually in quickstart Scenario 10. If focus is lost in practice, the follow-up is to keep a reference to the launched game and restore focus to its new position after the sort; this does not change the design above.

### Alternatives Considered
- *Connect `notify::last-played` on every game and re-sort on change*: Rejected. It adds one signal handler per game for a value that changes only on launch or load; an explicit call at the single launch point is simpler.
- *Remove and re-insert the item at position 0*: Rejected. It fights the sorter model and would break under other sort modes.

## 10. Non-Fatal Recording When Saving Fails (Follow-up 2026-10-08)

### Problem Statement
`Game.play()` records the launch before spawning the process (section 8). `play_history.record()` calls `mkdir`, writes a temporary file, and replaces the target, none of which handle `OSError`. Any storage problem (full disk, read-only or permission-denied data directory under a restrictive Flatpak sandbox, directory cannot be created, replace fails) therefore raises out of `Game.play()` and the game never starts (violates FR-022).

### Decision
- `record()` updates the cached mapping first, so the session state and any later successful save include the time (FR-023, spec edge case).
- The directory creation, temp-file write, and replace are wrapped in `try`/`except OSError`. On failure, `record()` logs one warning via the module logger (`logging.getLogger(__name__).warning(..., exc_info=...)` style used elsewhere in the project) naming the file and the error (FR-024), then returns normally.
- On failure, the temporary file is removed with `tmp.unlink(missing_ok=True)` in its own `OSError` guard, so a failed cleanup neither raises nor masks the original warning (FR-025). The existing target file is only ever touched by the final atomic replace, so it stays intact when anything earlier fails.
- `Game.play()` needs no ordering change: `last_played` is set before `record()`, `record()` no longer raises, and the process is then spawned and `exit-after-launch` handled as today (FR-022).

### Rationale
- Fixing it inside `record()` protects every present and future caller and keeps `Game.play()` free of storage concerns (Principle II).
- Catching `OSError` (the base of `PermissionError`, `FileNotFoundError`, and disk-full errors) covers the listed cases without a blanket `Exception` catch, keeping Ruff `BLE001` satisfied.
- Updating memory before writing means an earlier failed save is repaired by the next successful one.

### Alternatives Considered
- *Catch the error in `Game.play()`*: Rejected. Duplicates the guard at each call site and leaves `record()` unsafe for other callers.
- *Show an `Adw.Toast` or dialog on failure*: Rejected. The spec limits reporting to the log (assumption in spec); it would add a translated string and noise for a problem unrelated to what the user asked for.
- *Retry or queue the write in the background*: Rejected. Added complexity for a rare failure; the next launch's save already includes the missed time.
- *Catch `Exception`*: Rejected. Would hide programming errors such as `TypeError` from `json.dump`.

## 11. Show/Hide Game Titles (Amendment 2026-10-09)

### Findings
- The card title is the last child of `$GameItem` in `cartridges/ui/game-item.blp`: `Label { label: bind template.game as <$Game>.name; ellipsize: middle; }`.
- The placeholder shown for games without a cover (`cartridges/ui/cover.blp`, "icon" page) is only the application icon. It carries no text, so hiding every title would leave cover-less games unidentifiable. (Earlier spec wording that the placeholder "displays the title" is satisfied only by this label.)
- A `Gtk.Label` with `visible: false` is removed from the accessibility tree, so the card would lose its name for screen readers.
- Live-updating settings already have a pattern: `GameItem` connects `changed::cover-launches-game` in `__init__` and recomputes (`_update_action_button`). Switches in Preferences are bound declaratively by key name through `_bind_switches`, which resolves a template child named `<key with underscores>_switch`.

### Decision
1. Schema: add `<key name="show-game-titles" type="b"><default>true</default></key>` next to `cover-launches-game` in `data/page.samuelm333.Cartridges.gschema.xml.in`. Absent stored value means default `true`, so upgrading users see no change (FR-027).
2. Preferences: add `Adw.SwitchRow show_game_titles_switch` ("Show Game Titles", subtitle "Display the name under each cover in the library") in a new `Adw.PreferencesGroup` titled "Appearance" on `general_page`, between Behavior and Images. Add `"show-game-titles"` to the `switches` set in `_bind_switches` and the `Gtk.Template.Child()` declaration in `preferences.py` (FR-026, FR-028 persistence via GSettings).
3. Card: give the title label an id (`title_label`) and expose it as a template child. In `GameItem`, add `_update_title` that sets `title_label.set_visible(SETTINGS.get_boolean("show-game-titles") or self.game.cover is None)`; connect it to `changed::show-game-titles` and to the game's `notify::cover` (so adding or removing a cover updates the card), and call it once at setup and when `game` changes (FR-028, FR-029).
4. Accessibility: set the card's accessible label to the game name from `GameItem` (`update_property([Gtk.AccessibleProperty.LABEL], [name])`), refreshed when `game` changes and on the game's `notify::name`, so the name is exposed whether or not the label is visible (FR-029, SC-012). Blueprint's `accessibility { }` block was tried first, but it only accepts literal values; `label: bind ...` fails to compile (`Expected ;`), so this is done in Python.
5. No change to hover controls, toast, sorting, or filtering, which do not read the label (FR-030).

### Rationale
- Mirrors the established settings pattern, so it is the smallest, most consistent change.
- A GSettings key gives persistence and live updates for free, and an unset key defaults to the current behavior.
- Keeping titles for cover-less games avoids a real usability trap discovered in the code.

### Alternatives Considered
- *Hide the label with a CSS class*: Rejected. A visible-but-transparent label still takes layout space and stays in the accessibility tree inconsistently; toggling `visible` reflows the grid and is simpler.
- *Bind `visible` directly with `SETTINGS.bind`*: Rejected. It cannot express the "unless the game has no cover" rule without a custom mapping.
- *Show the title as a tooltip when hidden*: Rejected for now (spec assumption). The accessible name covers assistive technology; a tooltip can follow if requested.
- *Draw the title onto the placeholder cover instead*: Rejected. It changes the Cover widget used elsewhere (details, picker) for a card-only concern.
- *Per-collection or per-game control*: Out of scope (spec assumption).

### Open Verification (not a blocker)
How `Gtk.GridView` re-measures row heights when every card's label toggles at once is toolkit behavior. Verified manually in quickstart Scenario 12 with a large library; if rows do not reflow, call `queue_resize()` on the grid after the setting changes.

## 12. Full Titles Without Truncation (Amendment 2026-10-08)

### Findings
- `title_label` in `cartridges/ui/game-item.blp` is `Label { label: bind template.game as <$Game>.name; ellipsize: middle; }`. With `ellipsize` set and no `wrap`, the label reports a tiny minimum width and draws one line, cutting the middle of any name wider than its allocation. This is the reported defect.
- The card is a vertical `Gtk.Box` (`#game-item`, 12px CSS padding, 12px spacing): the cover `Overlay` first, then the label. `Cover` has a fixed 200x300 size enforced by `CoverLayoutManager`, so the cover's size cannot be influenced by its siblings.
- `Gtk.GridView` chooses the number of columns from the largest *minimum* item width and then shares the available width evenly between columns; each row is as tall as the tallest item measured at the column width (height-for-width). Text in a row with one long title therefore makes only that row taller.
- The keyboard and gamepad focus indicator is an outline on `#cover` (`style.css`), not on the whole card, so the label does not affect it.
- Names are displayed exactly as the source reports them; no source strips whitespace (only the details editor strips on save, `game_details.py`).

### Decision
1. In `game-item.blp`, replace `ellipsize: middle;` on `title_label` with:
   - `wrap: true;` so the label flows onto as many lines as needed, with no `lines` limit (FR-031, FR-032).
   - `wrap-mode: word_char;` so breaks happen between words, falling back to breaking inside a word only when the word alone is wider than the line (FR-032, acceptance scenario 4). Pango applies its own rules for scripts without spaces (CJK) and for right-to-left text.
   - `justify: center;` so every line is centered under the cover (FR-033). `xalign` stays at its default 0.5.
2. Do not set `max-width-chars`, `width-chars`, or a width request. The label then wraps at the width the grid already allocates to it, so a title that fit on one line before still fits on exactly one line (acceptance scenario 2), and columns are unchanged (FR-034).
3. With `word_char`, the label's minimum width is about one character, smaller than the 200px cover, so a long title cannot raise the grid's minimum column width or reduce the column count (FR-034, SC-014).
4. Bind the label through a display callback: `label: bind $_display_title(template.game as <$Game>.name) as <string>;`, with `GameItem._display_title(_this, name: str) -> str` returning `name.strip()`, following the `Cover._content_fit` static template-callback pattern. This removes leading and trailing blank lines and spaces (spec edge case) while keeping any line breaks inside the name. The accessible label from section 11 is left as the raw name, which screen readers already handle well.
5. No change to the visibility rule, the hover overlay, CSS, or the details view (FR-035, spec assumption).

### Rationale
- Purely declarative and local to one label; it relies on standard `Gtk.Label` wrapping (Principles III and IV) and needs no custom layout code.
- Wrapping at the existing allocation is the only option that keeps single-line titles identical to today and keeps column widths unchanged, as the spec's assumptions require.

### Alternatives Considered
- *Cap at two or three lines with an ellipsis*: Rejected. The request is "force all to show"; FR-031 forbids any truncation.
- *`wrap-mode: word`*: Rejected. A single word longer than the cell (concatenated names, URL-like titles) would raise the label's minimum width, widen every column, and could drop a column (violates FR-034).
- *`wrap-mode: char`*: Rejected. Breaks ordinary words mid-word even when a space is available, which reads poorly.
- *Constrain the label to the 200px cover width (width request or a custom layout manager)*: Rejected. It would make titles wrap earlier than today, so titles that fit on one line now would start wrapping, contradicting acceptance scenario 2, and it adds layout code for no user benefit.
- *Shrink the font for long titles*: Rejected in the spec assumptions; inconsistent typography and still fails for very long names.
- *Show the full title in a tooltip and keep the ellipsis*: Rejected. Not visible without hovering, unusable with keyboard or gamepad, and not what was asked.
- *Strip whitespace at the source or in `Game`*: Rejected for this amendment. It would change stored names and source modules (Principle II) for a purely presentational concern.

### Open Verification (not a blocker)
- The row-height behavior in Findings is how `Gtk.GridView` works in GTK 4.x, but the exact behavior is toolkit-internal. It is checked manually in quickstart Scenario 13 (mixed long and short titles in one row, window resizing). If a long title were to widen columns in practice, the fallback is `max-width-chars: 1` on the label, which caps its natural width while it still fills the allocated width.
- `Gtk.GridView` estimates the heights of rows it has not built yet, so in a very long library with many multi-line titles the scrollbar may shift slightly while scrolling. This is standard GridView behavior and is acceptable; the scenario records it if seen.
