# UI and Module Contracts: Game Import

**Feature**: [../spec.md](../spec.md) | **Data model**: [../data-model.md](../data-model.md)

## 1. Preferences: Import page (`cartridges/ui/preferences.blp`)

Order of groups on `import_page` after the change:

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

## 4. `cartridges/sources/__init__.py` (changed)

```python
def location(key: str, candidates: Iterable[Path]) -> Path: ...

class Source:
    def scan(self, added: int) -> Iterator[Game]: ...       # enable check + existing merge rules
    def replace_games(self, games: list[Game]) -> list[Game]: ...  # returns newly added games
```

Contract:
- `scan()` yields nothing for a disabled source.
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
