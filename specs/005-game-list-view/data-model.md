# Data Model & Component State: Main Game List View

**Branch**: `feat/005-game-list-view`
**Feature**: `specs/005-game-list-view`
**Date**: 2026-10-06

## 1. Entities & Data Models

### Game Entity (Reference)
- **Source**: `cartridges.games.Game`
- **Fields**:
  - `game_id` (str): Unique identifier for the game.
  - `name` (str): Display title of the game.
  - `developer` (str | None): Studio or publisher name.
  - `executable` (str): Executable path or URI command string.
  - `cover` (Gdk.Paintable | None): Loaded cover texture or placeholder.
  - `hidden` (bool): Visibility flag in main list.
  - `removed` (bool): Deletion marker.
  - `last_played` (int): Unix timestamp in seconds of the most recent launch, `0` if never played. After load it holds `max(launcher-reported, Cartridges-recorded)`; see section 5.
  - `added` (int): Unix timestamp when game was imported.

### GameItem Widget Model
- **Source**: `cartridges.ui.game_item.GameItem` (subclass of `Gtk.Box`)
- **Properties**:
  - `game` (`cartridges.games.Game`): Bound game instance.
  - `position` (int): Numerical index within the parent grid list model.
- **Children**:
  - `cover` (`cartridges.ui.cover.Cover`): Visual cover paintable.
  - `action_button` (`Gtk.Button`): Top-left circular overlay button.
  - `options` (`Gtk.MenuButton`): Top-right circular overlay menu button.
  - `collections_box` (`cartridges.ui.collections.CollectionsBox`): Collections sub-widget inside popover.
  - `motion` (`Gtk.EventControllerMotion`): Pointer tracking controller.
  - `title` (`Gtk.Label`): Centered title label beneath the cover picture.

## 2. Configuration Settings Model

### Settings Schema (`page.samuelm333.Cartridges`)
- **Key**: `cover-launches-game`
- **Type**: `b` (boolean)
- **Default**: `false`
- **Summary**: Swaps the behavior of the cover image and the hover play/info button.
- **Values**:
  - `false`: Cover click activates `game.details`; hover button activates `game.play`.
  - `true`: Cover click activates `game.play`; hover button activates `game.details`.

## 3. UI Component States and Transitions

### Hover & Visibility States

```text
+-----------------------+     Pointer enters card      +-----------------------+
|  Buttons Hidden       | ---------------------------> |  Buttons Visible      |
|  (.hidden class added)|                              |  (.hidden class rem.) |
|  can_focus = False    | <--------------------------- |  can_focus = True     |
+-----------------------+     Pointer leaves card      +-----------------------+
           ^                  (options.active == False)            |
           |                                                       | User clicks
           |                                                       | options button
           |                                                       v
           |                  Menu closed              +-----------------------+
           +------------------------------------------ |  Options Menu Open    |
                              (options.active == False)|  (options.active=True)|
                                                       |  Menu button retained |
                                                       +-----------------------+
```

### Preference State Transitions

```text
[cover-launches-game == False] (Default)
  - Cover click        -> Opens Game Details
  - Top-left button    -> Icon: "media-playback-start-symbolic"
                          Tooltip: "Play"
                          Action: "game.play"
                          Effect: Launches game

       | User toggles "Cover Image Launches Game" in Preferences
       v

[cover-launches-game == True]
  - Cover click        -> Launches Game
  - Top-left button    -> Icon: "help-about-symbolic"
  - Tooltip: "Details"
  - Action: "game.details"
  - Effect: Opens Game Details
```

## 4. Launch Toast Notification Model

### Toast Entity
- **Source**: `Adw.Toast` displayed on `Adw.ToastOverlay` in `cartridges.ui.window.Window`
- **Fields**:
  - `title` (str): Localized display message (`_("Launched {}").format(game.name)`).
  - `use_markup` (bool): `False`.
  - `priority` (Adw.ToastPriority): `Adw.ToastPriority.NORMAL` (default).
  - `timeout` (int): Standard system toast duration in seconds.

### Launch Feedback State Flow

```text
User triggers launch
(Hover Play button, Cover click when inverted, or Details view Play button)
       |
       v
cartridges.ui.games.play(game)
       |
       +---> game.play() (spawns game subprocess)
       |
       +---> _window().send_toast(_("Launched {}").format(game.name))
                 |
                 v
            Adw.Toast created and added to Adw.ToastOverlay
                 |
                 +---> Displayed at bottom of window
                 +---> Dismissable via user swipe or timeout
```

## 5. Play History Model (Amendment 2026-10-08)

### Play History Store
- **Source**: `cartridges.play_history` (new module)
- **Location**: `$XDG_DATA_HOME/cartridges/last-played.json` (`DATA_DIR / "last-played.json"`)
- **Format**: A single JSON object mapping `game_id` to a Unix timestamp in seconds.

```json
{
    "imported_0": 1791460800,
    "lutris_celeste_12": 1791475200,
    "steam_620": 1791489600
}
```

- **Validation rules**:
  - Keys are `game_id` strings; they are source-prefixed and therefore unique across sources.
  - Values must be non-negative integers; any other entry is ignored on load.
  - A missing, unreadable, or invalid file is treated as an empty mapping. Loading never raises and never blocks the library from loading (SC-009).
  - Entries for games that no longer exist are kept and ignored; they are harmless and let history return if the game is reinstalled.
- **Writes**: Whole-file atomic replace (temporary file in the same directory, then `os.replace`), synchronous, once per launch.

### Last-Played Value Lifecycle

```text
Application start
       |
       v
Source._get_games(added)
  for each game from the launcher:
    game.added       = game.added or added
    game.last_played = max(game.last_played,                     # launcher-reported (Steam) or 0
                           play_history.load().get(game_id, 0))  # Cartridges-recorded or 0
       |
       v
Gtk.SortListModel sorts with _sort (unchanged)
  "last_played": newest first; ties and 0 values ordered by name
       |
       |  User launches a game (any path)
       v
cartridges.ui.games.play(game)
  -> Game.play()
       1. last_played = int(time.time())
       2. play_history.record(game_id, last_played)   # saved before spawn and before exit-after-launch quit
       3. spawn process
       4. quit if exit-after-launch
  -> send "Launched {}" toast
  -> sorter.changed(Gtk.SorterChange.DIFFERENT)
       |
       v
"Last Played" mode: game moves to position 0 (also within active search/collection/hidden filters)
Other modes:        position unchanged
```

### Ordering Rules (unchanged comparator, documented for reference)

| Sort mode | Primary key | Direction | Tie-break |
|-----------|-------------|-----------|-----------|
| `last_played` | `last_played` (seconds) | Descending; `0` (never played) last | Name, ascending, ignoring case and a leading "The " |
| `a-z` / `z-a` | `name` | Ascending / descending | None needed |
| `newest` / `oldest` | `added` | Descending / ascending | Name, ascending |

### Save Failure Handling (Follow-up 2026-10-08)

The persisted file is a best-effort copy of the in-memory mapping. A failed save changes only the file, never the in-memory mapping or the launch.

```text
record(game_id, timestamp)
  1. cache[game_id] = timestamp          # always, so sort/label and later saves include it
  2. try: mkdir -> write temp -> replace
     except OSError:
        log one warning (file path + reason)
        remove temp file (best effort)
  3. return                              # never raises OSError
```

| State | Memory | Disk |
|-------|--------|------|
| Before launch | `{A: t1}` | `{A: t1}` |
| Launch B, save fails | `{A: t1, B: t2}` | `{A: t1}` (unchanged, no temp file) |
| Launch C, save succeeds | `{A: t1, B: t2, C: t3}` | `{A: t1, B: t2, C: t3}` |
| Restart after the failed save only | Loaded from disk: `{A: t1}` | `{A: t1}` (B's launch is not remembered) |

## 6. Show Titles Preference Model (Amendment 2026-10-09)

### Settings Schema addition (`page.samuelm333.Cartridges`)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `show-game-titles` | `b` | `true` | When false, the title label under each cover in the main game list is hidden (except for games without a cover). |

### Title Visibility Rule

```text
title visible = show-game-titles OR game has no cover
```

| `show-game-titles` | Game has cover | Title label | Accessible name of the card |
|--------------------|----------------|-------------|-----------------------------|
| true | yes | Visible | Game name |
| true | no | Visible | Game name |
| false | yes | Hidden | Game name |
| false | no | Visible | Game name |

### State Transitions

| Event | Effect |
|-------|--------|
| Switch toggled in Preferences | GSettings emits `changed::show-game-titles`; every `GameItem` recomputes the rule; the value is persisted by GSettings |
| Cover added to a cover-less game | `notify::cover` on the game; the card recomputes the rule (title hides if the setting is off) |
| Cover removed from a game | Same recompute (title appears) |
| Application restart | GSettings supplies the stored value; absent value yields `true` |

## 7. Title Presentation Model (Amendment 2026-10-08, full titles)

No stored data changes. `Game.name` is unchanged; only how the card renders it changes.

### Displayed Title

```text
displayed title = game.name with leading and trailing whitespace removed
```

| Input name | Displayed title |
|------------|-----------------|
| `"Celeste"` | `Celeste` (one line, unchanged from today) |
| `"Name\n"` (launcher trailing newline) | `Name` (no blank second line) |
| `"Part One\nPart Two"` | Two lines, the inner break is kept |
| Name wider than the cell | Wrapped onto as many lines as needed, never ellipsized |
| One word wider than the cell | Broken inside the word only where needed |

The accessible label of the card (section 6) remains the raw `game.name`.

### Card Layout Invariants

| Property | Rule |
|----------|------|
| Cover size | Always 200x300, independent of the title |
| Column count and width | Determined by the window width and cover width only; never by title length |
| Row height | Height of the tallest card in that row (cover + spacing + title lines) |
| Cover vertical position | Top of the card, so covers in a row are aligned |
| Title line alignment | Each line centered |

### State Transitions

| Event | Effect |
|-------|--------|
| Game renamed | `notify::name` re-evaluates the label binding; the label re-wraps and the row height is re-measured |
| Window resized / column count changes | Labels re-wrap at the new allocated width |
| `show-game-titles` toggled | Visibility rule from section 6 applies; a shown title is always shown in full |
