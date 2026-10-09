# Data Model: Game Import

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)

## 1. Source (existing, `cartridges/sources/__init__.py`)

A `Gio.ListModel` of `Game`, one per source module.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `str` | Module `ID`: `steam`, `lutris`, `heroic`, `itch`, `legendary`, `desktop`, `flatpak`, `imported`. Also the GSettings enable key, except `imported`. |
| `name` | `str` | Display name. |
| `icon_name` | `str` | `<id>-symbolic`. |
| `_games` | `list[Game]` | Current games. |

**New behavior**:
- `enabled` (derived, not stored): `True` for `imported`; otherwise `SETTINGS.get_boolean(id)`. A disabled source yields no games (FR-013).
- `scan(added: int) -> Iterator[Game]`: the existing `_get_games()` wrapper, plus the enable check. Applies the play-history `max()` and the `added` default (FR-003, FR-004).
- `replace_games(games: list[Game]) -> list[Game]`: applies a reconciliation (section 4) in place and emits one `items_changed`. Returns the newly added games.

**Initial load** (`Source.__init__`):

| Condition | Initial `_games` |
|-----------|------------------|
| `id == "imported"` | Always scanned. |
| `import-on-startup` is on | Scanned (today's behavior). |
| `import-on-startup` is off | Empty. |
| Scan raises `OSError` or `sqlite3.Error` | Empty (FR-005). |

## 2. Game (existing, `cartridges/games.py`)

No schema change. Field ownership during re-import:

| Field | Owner on re-import | Rule |
|-------|--------------------|------|
| `game_id` | Key | Identity for reconciliation. |
| `source` | Launcher | Unchanged for a kept game (same `game_id` implies same source). |
| `added` | Cartridges | Kept. New games get the import time if the launcher gives none. |
| `last_played` | Both | `max(existing, launcher, play history)`. |
| `cover` | Both | Kept if set; otherwise taken from the new scan. |
| `name`, `executable`, `developer` | User (editable) | Kept. |
| `hidden` | User | Kept in memory. On a fresh scan, set from `hidden_games` if the user has ever hidden or unhidden this game (section 7); otherwise the launcher's value. Changes are recorded in `hidden_games` (FR-019, FR-020). |
| `removed` | User | Launcher games: in memory only; a removed game is replaced by the fresh scan object on the next import (FR-021). Manually added games: saved to the game file on change (FR-022). |
| `blacklisted` | User | Kept. |

## 3. Import run (new, `cartridges/importer.py`)

A singleton `GObject.Object` exposed as `importer.state`.

| Field | Type | Notes |
|-------|------|-------|
| `running` | `bool` (GObject property) | `True` from start to finish of `import_games()`. Bound to the Preferences row stack and to the `app.import` action's enabled state. |

**State transitions**:

```text
idle --(app.import activated, running is False)--> running
running --(all sources processed)--> idle   [returns the newly added games]
running --(app.import activated)--> running         [ignored: action is disabled]
```

**`import_games() -> list[Game]`** (coroutine):
1. Set `running = True`. Take `added = int(time.time())`.
2. For each `Source` in `sources.model` except `imported`:
   a. If disabled, reconcile with an empty list (its games disappear, FR-013).
   b. Otherwise iterate `scan(added)`, yielding to the main loop every 25 games.
   c. On `OSError` / `sqlite3.Error`, leave the source unchanged and continue.
   d. Otherwise call `replace_games()` with the scanned list.
   e. Yield to the main loop.
3. Set `running = False` (in a `finally` block) and return the newly added `Game` objects.

The caller uses `len(result)` for the toast and passes `result` to the SteamGridDB cover fetch.

## 4. Reconciliation (new, pure function in `cartridges/importer.py`)

```text
reconcile(existing: list[Game], scanned: list[Game]) -> Reconciliation
  kept:    list[Game]  existing, not-removed games whose game_id is in scanned, merged per section 2, in existing order
  added:   list[Game]  scanned games whose game_id is not in existing, or whose existing game is removed, in scan order
  removed: list[Game]  existing games whose game_id is not in scanned, or that are marked removed
```

Invariants:
- `kept + added` has no duplicate `game_id` (SC-003). If a scan yields the same `game_id` twice, the first one wins (Steam already de-duplicates; this protects other sources).
- `kept` contains the original objects, not copies.
- An existing game with `removed` set is never in `kept`: it goes to `removed`, and the scanned game with its `game_id` goes to `added` (FR-021). Its other state is not carried over.
- Idempotence holds for games that are not `removed`; once a removed game has been replaced, the replacement is a normal kept game.
- `reconcile(x, scan)` followed by `reconcile(result, scan)` with the same scan gives `added == []` and `removed == []` (idempotent, SC-003).

The resulting list is `kept + added`.

## 5. Settings (`data/page.samuelm333.Cartridges.gschema.xml.in`)

| Key | Change | Type | Default | Used by |
|-----|--------|------|---------|---------|
| `auto-import` | Removed | | | |
| `import-on-startup` | New | `b` | `true` | `Source.__init__` (FR-017, FR-018) |
| `remove-missing` | Removed | | | (FR-016) |
| `steam`, `lutris`, `heroic`, `itch`, `legendary`, `desktop`, `flatpak` | Now honored | `b` | unchanged | `Source.enabled` (FR-013) |
| `steam-location`, `lutris-location`, `heroic-location`, `itch-location`, `legendary-location` | Now honored when user-set | `s` | unchanged | `sources.location()` (FR-014) |
| `lutris-import-steam`, `lutris-import-flatpak` | Now honored | `b` | `false` | `lutris.get_games()` (FR-015) |
| `heroic-import-epic`, `-gog`, `-amazon`, `-sideload` | Now honored | `b` | `true` | `heroic.get_games()` (FR-015) |
| `flatpak-*` | Already honored | | unchanged | `flatpak.get_games()` |
| `lutris-cache-location` | Unchanged, unused | `s` | unchanged | Not shown in Preferences; out of scope. |

## 6. Location resolution (new helper in `cartridges/sources/__init__.py`)

```text
location(key: str, candidates: Iterable[Path]) -> Path
```

| User has set `key` | Result |
|--------------------|--------|
| Yes | `Path(value).expanduser()`, whether or not it exists. A missing path makes the source raise `OSError` and yield no games. |
| No | First directory in `candidates` that exists (today's auto-detection, which already includes the schema default paths). |
| No, and none exist | Raises `FileNotFoundError`. |

| Source | Key | Candidates (unchanged from today) |
|--------|-----|-----------------------------------|
| Steam | `steam-location` | `steam._DATA_PATHS` |
| Lutris | `lutris-location` | `lutris._DATA_PATHS` |
| Heroic | `heroic-location` | `heroic._CONFIG_PATHS` |
| itch | `itch-location` | `itch._CONFIG_PATHS` |
| Legendary | `legendary-location` | `(legendary._CONFIG_PATH,)` |

## 7. Hidden-state store (new, `cartridges/hidden_games.py`)

Persisted at `DATA_DIR / "hidden.json"`:

```json
{
    "heroic_abc": true,
    "steam_620": false
}
```

| Field | Type | Notes |
|-------|------|-------|
| key | `str` | A `game_id`. Entries stay while the game is uninstalled. |
| value | `bool` | `True` if the user last hid the game, `False` if the user last unhid it. A missing key means the user never chose, so the launcher's value applies. |

API:
- `load() -> dict[str, bool]`: cached; tolerant of a missing, undecodable or invalid file; entries that are not `str -> bool` are skipped.
- `record(game_id: str, hidden: bool) -> None`: updates the cache, then writes atomically. A failed write is logged, never raised.

Lifecycle:
1. `Source.scan()` builds a game, then applies `load()` to set `hidden` for known IDs.
2. After that, `Source` connects `notify::hidden` on the game; each change calls `record()`.
3. `Source.append()` (a new manually added game) connects the same handler.

Removed games for manually added sources use the existing game file: `Source` also connects `notify::removed` for games whose `source == "imported"`, calling `Game.save()` and catching `OSError`.
