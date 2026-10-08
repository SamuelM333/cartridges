# UI Contracts: Main Game List View and Cover Interactions

**Branch**: `feat/005-game-list-view`
**Feature**: `specs/005-game-list-view`
**Date**: 2026-10-06

## 1. Widget Structure & Blueprint Contract

### Template Definition: `$GameItem`
- **Base Type**: `Gtk.Box`
- **Orientation**: `vertical`
- **Spacing**: `12`
- **CSS Name**: `game-item`

### Layout Contract

```blueprint
template $GameItem: Box {
  name: "game-item";
  orientation: vertical;
  spacing: 12;

  EventControllerMotion motion {
    notify::contains-pointer => $_reveal_buttons();
  }

  Overlay {
    halign: center;

    child: $Cover cover {
      paintable: bind template.game as <$Game>.cover;
    };

    [overlay]
    Button action_button {
      halign: start;
      valign: start;
      margin-top: 6;
      margin-start: 6;

      styles [
        "circular",
      ]
    }

    [overlay]
    MenuButton options {
      icon-name: "view-more-symbolic";
      tooltip-text: _("Options");
      halign: end;
      valign: start;
      margin-top: 6;
      margin-end: 6;
      notify::active => $_reveal_buttons();
      notify::active => $_setup_collections();

      popover: PopoverMenu {
        menu-model: menu {
          section {
            item (_("Edit"), "game.edit")
            item {
              label: _("Hide");
              action: "game.hide";
              hidden-when: "action-disabled";
            }
            item {
              label: _("Unhide");
              action: "game.unhide";
              hidden-when: "action-disabled";
            }
            item (_("Remove"), "game.remove")
          }
          section {
            item (_("New Collection"), "collection.add")
            item {
              custom: "collections";
            }
          }
        };
        // collections box ...
      };

      styles [
        "circular",
      ]
    }
  }

  Label {
    label: bind template.game as <$Game>.name;
    ellipsize: middle;
  }
}
```

## 2. Action Contract (`GameActions`)

The `GameItem` widget binds an action group mapped under the `"game"` prefix:

| Action Name | Scope | Parameter | Activation Result |
|-------------|-------|-----------|-------------------|
| `game.play` | Game instance | None | Invokes `games.play(game)`, launching game executable and displaying dismissable toast |
| `game.details` | Game instance | None | Navigates `navigation_view` to the `"details"` page for `game` |
| `game.edit` | Game instance | None | Navigates to `"details"` page in edit mode |
| `game.hide` | Game instance | None | Sets `game.hidden = True`, displays undo toast |
| `game.unhide` | Game instance | None | Sets `game.hidden = False`, displays undo toast |
| `game.remove` | Game instance | None | Sets `game.removed = True`, displays undo toast |

## 3. Dynamic Button State Contract

The `GameItem._update_action_button` method enforces the following contract upon initialization and `changed::cover-launches-game` notification:

| Setting `cover-launches-game` | Target Button | Icon Name | Tooltip | Action Name |
|-------------------------------|---------------|-----------|---------|-------------|
| `false` (Default) | `action_button` | `media-playback-start-symbolic` | `_("Play")` | `game.play` |
| `true` | `action_button` | `help-about-symbolic` | `_("Details")` | `game.details` |

## 4. CSS Styling & Transition Contract

From `cartridges/ui/style.css`:

```css
#game-item overlay > button,
#game-item overlay > menubutton > button {
  color: white;
  backdrop-filter: blur(9px) brightness(30%) saturate(600%);
  box-shadow:
    0 0 0 1px rgb(from currentcolor r g b / 10%) inset,
    0 1px rgb(from currentcolor r g b / 30%) inset;
  transition-property:
    outline-color, outline-width, outline-offset, background, box-shadow,
    opacity, transform;
}

#game-item overlay > button.hidden {
  opacity: 0;
  transform: translateY(-6px);
}

#game-item overlay > menubutton.hidden > button {
  opacity: 0;
  transform: translateY(-6px);
}
```

## 5. Launch Toast Notification Contract

The function `cartridges.ui.games.play(game: Game) -> None` provides the unified entry point for launching a game from the UI:

```python
def play(game: Game) -> None:
    """Launch `game` and notify the user with a toast."""
    game.play()
    # Translators: {} is the name of the game that was launched
    _window().send_toast(_("Launched {}").format(game.name))
```

- **Trigger Points**:
  - `game.play` action via hover button (`GameItem`) or details page (`GameDetails`).
  - Cover click on `GridView` item activation when `cover-launches-game` is true.
- **Toast Properties**:
  - Message: `_("Launched {}").format(game.name)`
  - Dismissable: Yes (standard Libadwaita `Adw.Toast` behavior).
- **Re-sort (amendment 2026-10-08)**: After `game.play()` returns, `play` calls `sorter.changed(Gtk.SorterChange.DIFFERENT)` so the launched game moves to the first position under the "Last Played" sort (FR-018). Other sort modes are unaffected (FR-021).

## 6. Play History Contract (Amendment 2026-10-08)

Module `cartridges.play_history` is a domain-layer module with no GTK widget imports.

| Function | Signature | Behavior |
|----------|-----------|----------|
| `load` | `load() -> dict[str, int]` | Returns the cached mapping of `game_id` to Unix seconds, reading `DATA_DIR / "last-played.json"` on first call. Missing or invalid file returns `{}`; invalid entries are skipped. Never raises. |
| `record` | `record(game_id: str, timestamp: int) -> None` | Sets `game_id` to `timestamp` in the cached mapping, then atomically rewrites the file. Synchronous. Never raises `OSError`: on a storage failure it logs one warning with the reason, removes the temporary file (best effort), leaves the existing file untouched, and returns normally (FR-022 to FR-025). |

### Callers

| Caller | Contract |
|--------|----------|
| `Game.play()` (`cartridges/games.py`) | MUST set `self.last_played = int(time.time())` and call `play_history.record(self.game_id, self.last_played)` before spawning the process and before any `exit-after-launch` quit. MUST NOT depend on `record()` succeeding: the process is always spawned afterwards. |
| `Source._get_games()` (`cartridges/sources/__init__.py`) | MUST set `game.last_played = max(game.last_played, play_history.load().get(game.game_id, 0))` for every yielded game. |
| Individual source modules (`cartridges/sources/*.py`) | MUST NOT read or write play history; they report only what their launcher knows. |

### Failure Handling Contract (Follow-up 2026-10-08)

| Condition | In-memory `last_played` / cache | Log | Files on disk | Launch |
|-----------|--------------------------------|-----|---------------|--------|
| Save succeeds | Updated | None | History file updated atomically | Proceeds |
| Directory cannot be created | Updated | One warning | Unchanged, no temp file | Proceeds |
| Temp-file write fails (disk full, permission denied, read-only) | Updated | One warning | Existing file unchanged, temp file removed | Proceeds |
| Replace fails | Updated | One warning | Existing file unchanged, temp file removed | Proceeds |
| Temp-file cleanup also fails | Updated | One warning (the original error) | Existing file unchanged | Proceeds |

## 7. Show Game Titles Contract (Amendment 2026-10-09)

### Preferences (`cartridges/ui/preferences.blp`)

- Page: `general_page` ("General"). New `Adw.PreferencesGroup` titled "Appearance" placed between "Behavior" and "Images".
- Row: `Adw.SwitchRow show_game_titles_switch`, title `_("Show Game Titles")`, subtitle `_("Display the name under each cover in the library")`.
- Binding: key `show-game-titles` is added to the `switches` set in `Preferences._bind_switches`, bound to `active` with `Gio.SettingsBindFlags.DEFAULT`.

### Game card (`cartridges/ui/game-item.blp`, `cartridges/ui/game_item.py`)

| Element | Contract |
|---------|----------|
| `GameItem._update_accessible_label` | MUST set the card's accessible label to the game name (`Gtk.AccessibleProperty.LABEL`) at setup, when `game` changes, and on the game's `notify::name`, so the name is exposed regardless of label visibility. Blueprint's `accessibility { }` block cannot bind and MUST NOT be used for this. |
| Title `Label` (id `title_label`) | Visible if and only if `show-game-titles` is true or `game.cover` is `None`. Keeps `ellipsize: middle`. |
| `GameItem._update_title` | Recomputes the visibility rule. MUST run at setup, on `changed::show-game-titles`, on `notify::cover` of the current game, and when `game` changes. Handlers on the previous game MUST be disconnected when `game` changes. |

### Non-regression

Hover buttons (sections 1 to 4), the launch toast (section 5), sorting and filtering MUST NOT read or depend on the title label or the new key.
