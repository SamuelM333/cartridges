# Quickstart Validation Guide: Manual Game Add

**Branch**: `feat/009-manual-game-add`
**Contracts**: [contracts/persistence-contract.md](contracts/persistence-contract.md) | **Data model**: [data-model.md](data-model.md)

## Prerequisites

- Build environment: the `gtk-dev` Distrobox container, as in the constitution.
- A throwaway data directory so real games are untouched:

```bash
export XDG_DATA_HOME=/tmp/cartridges-009/data
export XDG_CACHE_HOME=/tmp/cartridges-009/cache
mkdir -p "$XDG_DATA_HOME" "$XDG_CACHE_HOME"
```

- A built and installed copy of the app (see the build steps in `specs/005-game-list-view/quickstart.md`; note that edited `.blp` files must be recompiled by hand, but this feature changes none).
- The records live in `$XDG_DATA_HOME/cartridges/games/`; inspect with `ls` and `cat`.

## Automated checks

```bash
python3 tests/test_manual_games.py        # ID allocation, atomic save, failure cases, round trip
pre-commit run --all-files
ninja -C _build test
```

## Scenario 1: Added game survives a restart (US1, FR-002, FR-004, SC-001)

1. Start the app with an empty data directory. Choose Add Game; enter name `Test One`, command `true`, developer `Dev`, and pick a cover; Apply.
2. **Verify**: the game appears. `ls $XDG_DATA_HOME/cartridges/games/` shows `imported_0.json`; `cat` shows the name, command, developer, and `added`.
3. Close the app normally, reopen it. **Verify**: `Test One` is present with its developer and cover, and Play launches `true` with the "Launched Test One" toast.
4. Repeat steps 1 to 3, but end the process with `kill -9` right after pressing Apply. **Verify**: the game is still there on the next start (SC-004).

## Scenario 2: Startup import off and imports do not touch added games (US1, FR-005, FR-009, SC-005)

1. Turn off Import Games on Startup in Preferences; restart. **Verify**: `Test One` is still shown.
2. Run Import Now with at least one launcher enabled. **Verify**: `Test One` is unchanged, not duplicated, and no file in `games/` changes (compare `ls -l --time-style=full-iso` before and after).

## Scenario 3: Edits persist, cancel does not (US2, FR-003, SC-002)

1. Edit `Test One`: change name to `Test Uno`, command to `echo hi`, developer to `Dev2`; Apply. Restart. **Verify**: the new values are shown and the record has them.
2. Edit again, change the name, then Cancel. Restart. **Verify**: `Test Uno` is unchanged.
3. Replace the cover, Apply, restart. **Verify**: the new cover shows. Remove the cover, Apply, restart. **Verify**: the placeholder shows.

## Scenario 4: Other states persist (US2, FR-007, FR-010)

1. Hide the game, launch another game, and add the game to a new collection. Restart. **Verify**: it is still hidden, ordering by Last Played reflects the launch, and the collection still contains it.
2. Remove the game; restart. **Verify**: it stays removed. Remove another game and press Undo in the toast; restart. **Verify**: it is back.

## Scenario 5: Several added games stay distinct (US3, FR-008, SC-003)

1. Without restarting, add three games `A`, `B`, `C` with different commands. **Verify**: `imported_0.json`, `imported_1.json`, `imported_2.json` exist (numbers may start higher if earlier games exist), each with its own values.
2. Remove `B`, then add `D`. **Verify**: `D` gets a new number, `B`'s file still has `removed: true`, and `B` does not reappear after a restart.
3. Add ten games in a row, restart. **Verify**: all ten are present with correct values.

## Scenario 6: Failed save is visible and harmless (US4, FR-011, FR-012, SC-006)

1. With the app running, make the games directory unwritable: `chmod a-w "$XDG_DATA_HOME/cartridges/games"`.
2. Add `Locked One`. **Verify**: the game appears and launches, a toast "Locked One could not be saved and will be lost when Cartridges closes" appears within 1 second, the log contains one warning, no dialog appears, and `ls -a games/` shows no `*.tmp`.
3. Add `Locked Two`. **Verify**: it gets a different ID from `Locked One` while both are in the library (check the log message IDs, or hover details), even though neither file exists.
4. `chmod u+w` the directory and edit `Locked One`; Apply. **Verify**: no notice, and `imported_<n>.json` now contains the full state. Restart: **Verify**: `Locked One` is present, `Locked Two` is not (it was never saved).
5. Confirm earlier saved games are unchanged throughout.

## Scenario 7: Odd and damaged files (FR-013, FR-014)

1. Create `games/imported_old.json` containing `{}` and `games/imported_7.json` containing `not json`. Start the app and add a game. **Verify**: Add Game works, the new game does not take number 7, and both odd files are byte-for-byte unchanged afterwards.
2. Edit `imported_0.json` by hand while the app is closed (change `name`). Start the app. **Verify**: the edited name is shown.

## Scenario 8: Translation gate (FR-015)

```bash
ninja -C _build cartridges-pot
grep -n -B2 -A1 "could not be saved" po/cartridges.pot
```

**Verify**: the msgid appears with the `Translators:` comment and `{}` placeholder, with no extraction warnings.

## Cleanup

```bash
chmod -R u+w /tmp/cartridges-009; rm -rf /tmp/cartridges-009
```
