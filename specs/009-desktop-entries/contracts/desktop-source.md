# Contract: Desktop Entries source

**Feature**: [../spec.md](../spec.md) | **Data model**: [../data-model.md](../data-model.md)

Cartridges exposes no public API. This contract fixes the observable behavior of the Desktop Entries source, and of the shared code it relies on, so that it can be verified by `tests/test_desktop.py` and `tests/test_importer.py`.

## C-1: `cartridges.sources.desktop`

```python
ID: Final = "desktop"
NAME: Final = _("Desktop")
REFRESH_COVERS: Final = True

def get_games() -> Generator[Game]: ...
```

| Given entry | Then `get_games()` |
|-------------|--------------------|
| `Categories` lacks `Game` | does not yield it |
| `NoDisplay=true` or `Hidden=true` | does not yield it |
| file name matches the blacklist | does not yield it |
| `Exec` starts with a blacklisted prefix | does not yield it |
| has `X-Flatpak` | does not yield it |
| `TryExec` not found | does not yield it |
| unreadable, or no `Name` / `Exec` | does not yield it, and continues with other entries |
| same file name in two search folders | yields only the first, in search order |
| otherwise | yields a `Game` per [data-model.md section 2](../data-model.md) |

Icon outcomes (cover is never `image-missing`):

| `Icon=` | Cover shows |
|---------|-------------|
| (missing) | default application icon |
| installed theme name (for example `steam`, found in hicolor) | that icon |
| installed name with extension (`steam.png`) | that icon |
| unknown name | default application icon |
| installed only in a `pixmaps` folder (for example `cupsprinter`) | that icon |
| path (contains `/`) to a valid PNG or SVG | that image |
| path, file missing | default application icon |
| path, file is not an image | default application icon |

## C-2: `cartridges.cover.custom`

```python
def custom(game_id: str) -> Gdk.Paintable | None:
    """Load the cover the user chose for the game with `game_id`, if any."""
```

Returns `at_path(COVERS_DIR / f"{game_id}.gif") or at_path(COVERS_DIR / f"{game_id}.tiff")`.

## C-3: `cartridges.sources.Source.scan`

For each game from the module:
- `game.cover = cover.custom(game.game_id) or game.cover`
- if the module's `REFRESH_COVERS` is true: `saved_library.forget_cover(game.game_id)`

All existing behavior (hidden state, last played, added time, tracking) is unchanged.

## C-4: `cartridges.importer.reconcile`

```python
def reconcile(
    existing: Sequence[Game],
    scanned: Iterable[Game],
    *,
    refresh_covers: bool = False,
) -> Reconciliation: ...
```

`Source.replace_games` passes `refresh_covers=getattr(self._module, "REFRESH_COVERS", False)`.

| `refresh_covers` | existing cover | scanned cover | kept game's cover after |
|------------------|----------------|---------------|-------------------------|
| False | None | X | X |
| False | A | X | A |
| True | A | X | X |
| True | A | None | A |
| either | None | None | None |
