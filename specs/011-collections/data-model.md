# Data Model: Collections

**Feature**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Collection

A named, iconed group of games. It refers to games by identity and never copies them.

| Field | Type | Rules |
|-------|------|-------|
| `name` | string | Not empty to be applied in the dialog; a name of only spaces is accepted; not unique. |
| `icon` | string | One of 21 icon names: `collection` (default), `star`, `heart`, `music`, `people`, `skull`, `private`, `globe`, `map`, `city`, `car`, `horse`, `sprout`, `step-over`, `gamepad`, `ball`, `puzzle`, `flashlight`, `knife`, `gun`, `fist`. |
| `game-ids` | set of strings | Game identities, in no order. A manually added game's id is dropped at the next start if the game no longer exists; every other id is kept, installed or not. |
| `removed` | boolean | True after the user removes the collection. |

**Stored form**: the existing GSettings key `collections` of type `aa{sv}`, one dictionary per collection with the keys `name` (`s`), `icon` (`s`), `game-ids` (`as`), and `removed` (`b`). It is written after every change. This feature does not change it.

**States**:

```text
(created) --apply--> active --remove--> removed --undo--> active
                        |                  |
                        |                  +--next start--> (gone: skipped on load, then saved without it)
                        +--edit name/icon--> active
```

**Load rules**: an entry with `removed` true is skipped; an entry missing `name`, `icon`, or `game-ids` (or with the wrong type) is skipped and one warning is logged; the other entries load.

## Hidden game

The existing per-game flag, kept in `hidden.json` across restarts. Unchanged by this feature, which only changes where hidden games are listed.

## Preference: Hidden games show in Collections

| Field | Value |
|-------|-------|
| Key | `hidden-games-in-collections` in the main schema of each build |
| Type | boolean |
| Default | `false` |
| Written by | The Preferences switch only (the window reads it one way) |
| Reset by | `Reset App`, with all other keys |

## Derived rule: is a game listed in the main grid?

Defined in [contracts/visibility-rules.md](contracts/visibility-rules.md). Inputs: the game's `hidden` flag, `Show Hidden Games` (which lists only hidden games), the open collection (if any) and whether the game is in it, and this preference.
