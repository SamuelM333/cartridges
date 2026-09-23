# Data Model: GSettings Configuration, Flatpak Game Model, and SteamGridDB Runtime State

This document defines configuration schemas, data structures, and runtime models used by the Preferences dialog, individual modular game sources, Flatpak discovery, and SteamGridDB cover operations.

## 1. GSettings Preferences Schema

All configuration options are stored under the primary app ID schema namespace (`page.samuelm333.Cartridges`), enabling automatic bindings to Gtk and Adw row controls.

### General Options (Behavior & Images)

| Key Name | Type | Default | Description |
|----------|------|---------|-------------|
| `exit-after-launch` | `b` | `false` | If true, close Cartridges window and exit the process when any game starts. |
| `cover-launches-game` | `b` | `false` | If true, clicking a game cover starts the game directly; clicking the play button opens details dialog. |
| `high-quality-images` | `b` | `false` | If true, downloaded images are saved losslessly (deflate vs lzw TIFF) in the cache. |

### Import Options

| Key Name | Type | Default | Description |
|----------|------|---------|-------------|
| `auto-import` | `b` | `false` | Automatically trigger library scans on application startup. |
| `remove-missing` | `b` | `true` | Automatically prune/mark as removed any games that are no longer detected on disk. |

### Source Control Options

| Key Name | Type | Default | Description |
|----------|------|---------|-------------|
| `steam` | `b` | `true` | Enable Steam game source scanning. |
| `steam-location` | `s` | `"~/.steam/steam"` | The local filesystem installation folder for Steam library. |
| `lutris` | `b` | `true` | Enable Lutris game source scanning. |
| `lutris-location` | `s` | `"~/.var/app/net.lutris.Lutris/data/lutris/"` | Local Lutris data installation directory. |
| `lutris-cache-location` | `s` | `"~/.var/app/net.lutris.Lutris/cache/lutris"` | Local Lutris cover cache location. |
| `lutris-import-steam` | `b` | `false` | If true, import Steam games managed inside Lutris. |
| `lutris-import-flatpak` | `b` | `false` | If true, import Flatpak games managed inside Lutris. |
| `heroic` | `b` | `true` | Enable Heroic Games Launcher source scanning. |
| `heroic-location` | `s` | `"~/.config/heroic/"` | Local Heroic configuration folder. |
| `heroic-import-epic` | `b` | `true` | Import Epic Games Store games from Heroic. |
| `heroic-import-gog` | `b` | `true` | Import GOG games from Heroic. |
| `heroic-import-amazon` | `b` | `true` | Import Amazon Prime games from Heroic. |
| `heroic-import-sideload` | `b` | `true` | Import manually sideloaded games from Heroic. |
| `itch` | `b` | `true` | Enable Itch.io source scanning. |
| `itch-location` | `s` | `"~/.var/app/io.itch.itch/config/itch/"` | Local Itch library configuration folder. |
| `legendary` | `b` | `true` | Enable Legendary CLI source scanning. |
| `legendary-location` | `s` | `"~/.config/legendary/"` | Local Legendary configuration folder. |
| `desktop` | `b` | `true` | Enable desktop shortcuts (XDG Desktop entries) source. |
| `flatpak` | `b` | `true` | Enable Flatpak applications source scanning. |
| `flatpak-system-location` | `s` | `"/var/lib/flatpak/"` | Filesystem root for system-wide Flatpak installations. |
| `flatpak-user-location` | `s` | `"~/.local/share/flatpak/"` | Filesystem root for user-wide Flatpak installations. |
| `flatpak-import-launchers` | `b` | `false` | If true, scan and import known game launcher Flatpaks. |

### SteamGridDB Configuration Options

| Key Name | Type | Default | Description |
|----------|------|---------|-------------|
| `sgdb-key` | `s` | `""` | Personal API Key for SteamGridDB queries. |
| `sgdb` | `b` | `false` | If true, query SteamGridDB for missing game artwork. |
| `sgdb-prefer` | `b` | `false` | If true, download and use SteamGridDB covers even if official ones are present. |
| `sgdb-animated` | `b` | `false` | If true, query and download animated covers (GIF) from SteamGridDB. |

---

## 2. Flatpak Game Model

When Flatpak applications are discovered, they are instantiated as standard `Game` objects with the following schema mappings:

| Attribute | Field Value | Description |
|-----------|-------------|-------------|
| `game_id` | Application ID, e.g. `org.gnome.Games` | Unique identifier used as the key for persistent JSON. |
| `name` | Desktop Entry Name, e.g. `GNOME Games` | User-facing title. |
| `executable` | `"flatpak run org.gnome.Games"` | Shell launch command. |
| `source` | `"flatpak"` | Indicates source origin. |
| `added` | Epoch timestamp | Time of initial library detection. |
| `developer` | Desktop entry developer metadata | Developer attribution (where present). |
| `hidden` | `false` | Library visibility status. |
| `removed` | `false` | Deleted/pruned flag. |
| `blacklisted` | `false` | Ignored applications flag. |

---

## 3. SteamGridDB Real-Time Progress State Model

During asynchronous bulk updating of game covers, runtime state is tracked and projected onto UI widgets:

| Field Name | Type | Description |
|------------|------|-------------|
| `active_game_name` | `str` | Name of the game currently being queried on SteamGridDB. |
| `current_index` | `int` | Current 1-based index in the queue of games to update. |
| `total_games` | `int` | Total count of eligible games to update in this pass. |
| `fraction` | `float` | Progress fraction `(current_index / total_games)` between 0.0 and 1.0. |
| `success_count` | `int` | Number of game covers successfully retrieved and persisted. |
| `state` | `enum` | `IDLE`, `SCANNING`, `UPDATING`, `FINISHED`, `AUTH_ERROR`. |

---

## 4. Cover Picker Grid Artwork Option Model

When browsing alternative covers in `CoverPicker`:

| Field Name | Type | Description |
|------------|------|-------------|
| `id` | `int` | Unique SteamGridDB grid artwork identifier. |
| `url` | `str` | Direct HTTPS URL to full-resolution artwork image. |
| `thumb` | `str` | Direct HTTPS URL to thumbnail preview. |
| `author` | `dict` | Author object containing `name` and `steam64`. |
| `score` | `int` | Net community upvote/downvote score. |
| `style` | `str` | Style classification (alternate, blurred, material, no_logo). |
| `animated` | `bool` | True if the artwork is animated. |
| `aspect_ratio` | `float` | Fixed 2:3 ratio (`200 / 300`) rendered as 120x180 card without text tags. |

---

## 5. Staged Cover Editing Model & Legacy Overlay Controls

When editing a game's artwork in the Edit Game page overlay:

| Field Name | Type | Description |
|------------|------|-------------|
| `_staged_cover_paintable` | `Gdk.Paintable \| None` | In-memory paintable currently displayed on the cover widget in Edit mode. |
| `_staged_cover_path` | `Path \| None` | Local image file path staged for copy/conversion, or None if unchanged or unlinked. |
| `_staged_cover_action` | `str` | Staging state: `"unchanged"`, `"set"`, or `"remove"`. |
| `_original_cover_paintable`| `Gdk.Paintable \| None` | Reference to original cover paintable before entering Edit mode (restored on Cancel). |
| `original_cover_path` | `str` | Preserved reference/path to initial post-import cover image (`<game_id>.orig.tiff`). |
| `sgdb_candidates` | `list[dict]` | List of retrieved cover candidates from SteamGridDB (capped at max 10). |
| `status_message` | `str` | Text content of the dismissable post-update message in Preferences. |
| `status_visible` | `bool` | Visibility state of the post-update status banner in Preferences. |
