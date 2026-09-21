# Data Model: GSettings Configuration and Flatpak Game Model

This document defines the configuration schemas and data structures used by the Preferences dialog, individual modular game sources, and Flatpak game models.

## 1. GSettings Preferences Schema

All configuration options are stored under the primary app ID schema namespace (`page.samuelm333.Cartridges`), enabling automatic bindings to Gtk and Adw row controls.

### General Options (Behavior & Images)

| Key Name | Type | Default | Description |
|----------|------|---------|-------------|
| `exit-after-launch` | `b` | `false` | If true, close Cartridges window and exit the process when any game starts. |
| `cover-launches-game` | `b` | `false` | If true, clicking a game cover starts the game directly; clicking the play button opens the details dialog. |
| `high-quality-images` | `b` | `false` | If true, downloaded images are saved losslessly (e.g. as tiff/png) in the cache. |

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
| `sgdb-animated` | `b` | `false` | If true, query and download animated covers (APNG/GIF) from SteamGridDB. |

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

