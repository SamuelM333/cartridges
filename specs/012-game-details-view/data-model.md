# Data Model: Game Details View

Nothing is stored or changed on disk by this feature. The entities below are runtime objects.

## Game (existing, `cartridges/games.py`)

Shown by the details view. Fields used: `name`, `developer`, `executable`, `cover`, `last_played`, `added`, `hidden`, `removed`, `game_id`. Unchanged by this feature.

## Toast (existing, `Adw.Toast`)

| Field | Value |
|-------|-------|
| title | The message, shown as plain text (`use_markup=False`) |
| button label | "Undo" when an undo callback is given, otherwise none |
| priority | High when it has Undo, otherwise normal |

**Owner view** (new rule): the page that was visible when `Window.send_toast` was called, either the library page (`"games"`) or the details page (`"details"`). A toast is only ever added to its owner view's overlay.

### Lifecycle

```text
send_toast called
   -> details page visible? -> added to the details overlay
   -> otherwise              -> added to the library overlay

details overlay toast:  shown -> times out, closed by the user, or dismissed when the details page starts hiding
library overlay toast:  shown -> times out or closed by the user (unchanged)
```

## Undo history (existing, `Window._history`)

Maps each toast with Undo to its callback. Unchanged: entries are added by `send_toast` and used by the toast's Undo button and by Ctrl+Z, whichever overlay the toast is in.
