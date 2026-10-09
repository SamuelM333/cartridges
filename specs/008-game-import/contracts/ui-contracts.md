# UI and Module Contracts: Game Import

**Feature**: [../spec.md](../spec.md) | **Data model**: [../data-model.md](../data-model.md)

## 1. Preferences: Import page (`cartridges/ui/preferences.blp`)

Order of groups on `import_page` after the change:

0. Preferences wording: `import_on_startup_switch` gets a subtitle, `_("Scan for new games when Cartridges starts. When off, the games from your last import are shown.")` (FR-025).
1. **New untitled group** containing one row:
   - `Adw.ActionRow import_now_row`
     - title: `_("Import Now")`
     - subtitle: `_("Scan your sources for new and uninstalled games")`
     - suffix: `Gtk.Stack import_stack` with children
       - `Button import_button`, label `_("Import")`, `valign: center`, `action-name: "app.import"`
       - `Adw.Spinner import_spinner`, `valign: center`
2. **Behavior** (`import_behavior_group`), now containing only:
   - `Adw.SwitchRow import_on_startup_switch`, title `_("Import Games on Startup")`
   - (`remove_missing_switch` removed)
3. **Sources** (`sources_group`), unchanged.

Controller (`cartridges/ui/preferences.py`):
- Template children: add `import_stack`, `import_button`, `import_spinner`; rename `auto_import_switch` to `import_on_startup_switch`; remove `remove_missing_switch`.
- `_bind_switches`: replace `"auto-import"` and `"remove-missing"` with `"import-on-startup"`.
- On construction, bind `importer.state.running` to the stack: `True` shows `import_spinner`, `False` shows `import_button`. Use `SYNC_CREATE`, so a dialog opened during a running import shows the spinner.

## 2. Application action (`cartridges/application.py`)

| Action | Parameter | Enabled | Effect |
|--------|-----------|---------|--------|
| `app.import` | none | `not importer.state.running` | Starts `importer.import_games()` as an asyncio task. |

On completion of the task:
- Send a toast to the active window (if any) using `Window.send_toast()`:
  - `n > 0`: `ngettext("{} new game imported", "{} new games imported", n).format(n)`
  - `n == 0`: `_("No new games found")`
- If SteamGridDB is enabled and a key is set, run the cover fetch for the newly added games only.

No keyboard shortcut is added. The main window's "+" button keeps `action-name: "game.add"` (FR-012).

## 3. `cartridges/importer.py` (new)

```python
class ImportState(GObject.Object):
    running: bool  # GObject.Property, default False

state: ImportState

class Reconciliation(NamedTuple):
    kept: list[Game]
    added: list[Game]
    removed: list[Game]

def reconcile(existing: Sequence[Game], scanned: Iterable[Game]) -> Reconciliation: ...

async def import_games() -> list[Game]:
    """Re-scan every source except manually added games.

    Return the games that were not in the library before.
    """
```

Contract:
- `import_games()` must not be awaited concurrently; callers check `state.running` (the action does this through its enabled state).
- `state.running` is reset to `False` even if a source raises an unexpected exception.
- It never touches the `imported` source.
- `reconcile()` returns a game as `added` (not `kept`) when the existing game with that `game_id` has `removed` set, so a removed launcher game comes back as a new game on the next import (FR-021).

## 4. `cartridges/sources/__init__.py` (changed)

```python
def location(key: str, candidates: Iterable[Path]) -> Path: ...

class Source:
    def scan(self, added: int) -> Iterator[Game]: ...       # enable check + existing merge rules
    def replace_games(self, games: list[Game]) -> list[Game]: ...  # returns newly added games
```

Contract:
- `scan()` yields nothing for a disabled source.
- `scan()` sets `game.hidden` from `hidden_games.load()` when the game has an entry, then connects the change handlers (section 4a) before yielding it.
- `Source.append()` connects the same handlers.
- `Source.__init__` scans only if the source is `imported` or `import-on-startup` is on; it catches `OSError` and `sqlite3.Error`.
- `replace_games()` emits exactly one `items_changed` per call, or none if nothing changed.

## 5. Source modules (changed)

| Module | Change |
|--------|--------|
| `steam.py` | `_data_dir()` returns `location("steam-location", _DATA_PATHS)`. |
| `lutris.py` | `_data_dir()` returns `location("lutris-location", _DATA_PATHS)`. Runner filtering moves from SQL to Python and honors `lutris-import-steam` / `lutris-import-flatpak`. |
| `heroic.py` | `_config_dir()` returns `location("heroic-location", _CONFIG_PATHS)`. `get_games()` skips store classes whose sub-option is off. |
| `itch.py` | `_config_dir()` returns `location("itch-location", _CONFIG_PATHS)`. |
| `legendary.py` | `_config_dir()` returns `location("legendary-location", (_CONFIG_PATH,))`. |
| `flatpak.py` | Remove its own `flatpak` enable check (now done by `Source`). Otherwise unchanged. |
| `desktop.py`, `imported.py` | Unchanged. |

## 6. Settings schema (`data/page.samuelm333.Cartridges.gschema.xml.in`)

```xml
<key name="import-on-startup" type="b">
  <default>true</default>
</key>
```

Remove the `auto-import` and `remove-missing` keys.

## 4a. Hidden and removed state handlers (`cartridges/sources/__init__.py`, `cartridges/hidden_games.py`)

```python
# cartridges/hidden_games.py (new)
def load() -> dict[str, bool]: ...
def record(game_id: str, hidden: bool) -> None: ...
```

Handlers connected by `Source` on each game it exposes:

| Signal | Applies to | Effect |
|--------|------------|--------|
| `notify::hidden` | every game | `hidden_games.record(game.game_id, game.hidden)` |
| `notify::removed` | games with `source == "imported"` | `game.save()`; `OSError` is logged and swallowed |

Contract:
- Handlers are connected after the game's initial state is set, so loading never writes.
- `ui/games.py` is unchanged: `hide`, `unhide`, `remove` and their Undo callbacks set the properties and the handlers do the saving.
- `ui/preferences.py` stops calling `game.save()` itself in Remove All and its Undo.
- No user-visible strings are added.

## 7. `cartridges/saved_library.py` and `cover.save()` (amendment 2026-10-10)

```python
# cartridges/saved_library.py (new)
def read() -> dict[str, list[Game]]: ...   # cached; keyed by source ID; never raises
def request_save() -> None: ...             # sets the dirty flag; starts one save task if none is running
async def write(games: Iterable[Game]) -> None: ...  # library.json, then missing covers in batches, then prune

# cartridges/cover.py (changed)
def save(paintable: Gdk.Paintable, path: Path) -> bool: ...  # False if it could not be written
```

Contract:
- `read()` returns games that are ready to show: `hidden` and `last_played` already adjusted, covers loaded from `library-covers/`. It never raises; damaged data gives fewer games (FR-028).
- `request_save()` is safe to call from any change handler on the main thread. It never blocks and never raises. Several calls before the task runs produce one write.
- `write()` collects nothing itself; the task passes it every game in `sources.model` except `imported`, minus games with `removed` set. `OSError` while writing is logged and swallowed. The JSON file is replaced atomically; cover files are written before the task ends but after the JSON, so the game list is never behind its covers by more than one write.
- `write()` yields to the main loop after every 25 covers written.
- `Source` calls `saved_library.read()` for its own source ID in `__init__`, and connects `notify::removed` (launcher games) and `notify::cover` handlers that call `request_save()`.
- `importer.import_games()` calls `request_save()` once after the last source is processed. `sources.load()` calls it once after startup when `import-on-startup` is on.
- `cover.save()` writes a PNG: from the `PIL` image for a `_PILPaintable` (current frame for an animated image), by drawing the paintable at `WIDTH` x `HEIGHT` for any other paintable. It is the only new function in `cover.py`.
- No new action, signal, setting or dialog is added.
