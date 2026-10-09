# Data Model: Manual Game Add

**Branch**: `feat/009-manual-game-add`
**Date**: 2026-10-09

## 1. Saved Game Record

One JSON file per manually added game, in the existing format. No fields are added or renamed, so files written by earlier versions keep loading and files written now stay readable by earlier versions.

Location: `$XDG_DATA_HOME/cartridges/games/<game_id>.json`, where `game_id` is `imported_<n>`.

| Field | Type | Set by | Notes |
|-------|------|--------|-------|
| `game_id` | string | Add Game | `imported_<n>`, unique, never reused (section 2) |
| `source` | string | Add Game | Always `imported` |
| `name` | string | User | Required, non-empty (enforced by the form) |
| `executable` | string | User | Required, non-empty (enforced by the form) |
| `developer` | string | User | Optional |
| `added` | integer | Add Game | Unix time of first Apply; never changed by edits |
| `last_played` | integer | Launch | Merged on load with `last-played.json` (newest wins) |
| `hidden` | boolean | Hide/Unhide | `hidden.json` overrides this on load |
| `removed` | boolean | Remove/Undo | Permanent across restarts |
| `blacklisted` | boolean | existing | Unchanged |
| `version` | number | existing | Files with a newer version are skipped, not overwritten |

The cover is not part of the record: it lives in `COVERS_DIR` as `<game_id>.gif` or `<game_id>.tiff` (plus `.orig.tiff` backup) and is linked by `game_id`.

### Write rules
- Every save writes all fields above from the in-memory game (full state, never a patch), so a save after a failed one repairs the file (FR-012).
- The file is replaced atomically; a crash or failure leaves the previous file or no file, never a half-written one.
- Keys sorted, indent 4, UTF-8, as today (FR-014).

### Read rules (unchanged)
- Unreadable, invalid JSON, wrong types, missing required fields, or a newer `version`: the file is skipped and not touched.

## 2. Identity Allocation

```text
used     = { n : file stem matches "imported_<digits>" } union { n : id in taken matches the same form }
new id   = "imported_" + lowest non-negative integer not in used
```

| Input | Effect on numbering |
|-------|---------------------|
| `imported_3.json` valid | 3 is used |
| `imported_4.json` damaged or unsupported version | 4 is used (reserved, file untouched) |
| `imported_5.json` with `removed: true` | 5 is used (never reused, FR-008) |
| `imported_old.json`, `imported_.json`, `imported_1a.json` | Ignored for numbering, never parsed as numbers (FR-013) |
| Game in memory with ID `imported_6` whose save failed | 6 is used via `taken` |

`taken` is the set of `game_id` values of the games currently in the `imported` source model.

## 3. State Transitions

| Event | In memory | On disk |
|-------|-----------|---------|
| Apply on a new game | Game added to the `Added` source with the entered values | Record written (atomic). On failure: warning logged, toast shown, no file |
| Apply on an existing manual game | Name/command/developer updated | Record rewritten (atomic) |
| Cancel on add or edit | No game created / no change | No change |
| Cover set or removed, then Apply | Cover changed | Cover file changed as today; record rewritten by the same Apply |
| Hide / Unhide | `hidden` flips | `hidden.json` updated; record updated only if the existing removal handler fires |
| Launch | `last_played` set | `last-played.json` updated (feature 005) |
| Remove / Undo | `removed` flips | Record rewritten (existing handler); failure logged only |
| Add to / remove from collection | Collection updated | GSettings `collections` updated; kept on restart because the record exists |
| Import Now / startup import | `imported` source not scanned for changes | No change |
| Application restart | `imported_*.json` files loaded into the `Added` source, covers reattached | Unchanged |
| Remove All Games (feature 002) | Games cleared | Records and covers deleted, as already specified |

## 4. Failure Handling

| Failure | Behavior |
|---------|----------|
| Cannot create the data directory | `OSError` from `save()`; log one warning; toast; game works in memory |
| Cannot write the temporary file (full, read-only, denied) | Same; temporary file removed if created; previous record unchanged |
| Cannot replace the target | Same; temporary file removed |
| Cleanup of the temporary file fails | Ignored; the original error is the one reported |
| A later save succeeds | Full current state written; the game is persisted from then on |
| Closing the application after a failed save | The game is lost; the user was told when it happened |
