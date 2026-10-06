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
  - `last_played` (int): Unix timestamp of last execution.
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

```
