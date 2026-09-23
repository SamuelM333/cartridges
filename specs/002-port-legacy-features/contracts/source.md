# Contract: Modular Game Source Interface

This document specifies the contract governing game source providers in Cartridges (subclasses of `cartridges.sources.Source`).

## 1. Class Hierarchy and Protocol

Each modular source (e.g., `FlatpakSource`, `SteamSource`, `LutrisSource`) must inherit from `cartridges.sources.Source` and implement the following contract:

```python
class Source(Gio.ListStore, Gtk.SectionModel):
    name: str          # User-facing identifier for source (e.g., "flatpak", "steam")
    display_name: str  # Localized display name (e.g., _("Flatpak"))
    icon_name: str     # Symbolic icon name for UI presentation
```

## 2. Required Methods

### `load(self) -> None`
* **Description**: Discovers games from the source's local paths, parses metadata, instantiates `Game` objects, and populates the source's internal list store via `self.append(game)`.
* **Execution**: Must execute cleanly without raising unhandled exceptions. Path scanning must tolerate non-existent or inaccessible directories gracefully.

### `get_games(self) -> list[Game]`
* **Description**: Returns all currently discovered and loaded `Game` instances.

## 3. Game Object Properties

Games produced by a `Source` must conform to the following interface:

* `game_id: str`: Unique deterministic identifier prefixed or formatted per source (e.g. `flatpak_{app_id}`).
* `name: str`: Display title for library sorting and visual labels.
* `executable: str`: Command line or portal trigger to launch the game.
* `source: str`: Identifier matching `source.name`.
* `cover: Optional[Cover]`: Attached cover art (or None if pending artwork).
* `hidden: bool`: Whether user has hidden this game.
* `removed: bool`: Whether game was marked removed.
* `blacklisted: bool`: Whether game is suppressed from import.
