# Research: Collections

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## R1. How to list hidden games in an open collection

- **Decision**: Keep the existing hidden-games `BoolFilter` and wrap it in a `Gtk.AnyFilter` together with a new `HiddenInCollectionFilter`. The grid's `Gtk.EveryFilter` then reads: collection membership AND search AND (the existing hidden rule OR the new filter). Note what the existing rule is: with Show Hidden Games off it lists the games that are not hidden, and with it on it lists **only** the hidden games (the `BoolFilter` is inverted by the setting). `HiddenInCollectionFilter` ignores the item: it matches everything when a collection is set, its `enabled` property is true, and its `hidden_only` property (bound to Show Hidden Games) is false, and nothing otherwise. The `hidden_only` property is needed because without it the new filter would also list the games that are not hidden in the hidden-only view.
- **Rationale**: The existing expression-based `BoolFilter` is what makes the grid update the moment a game is hidden or unhidden (the model uses `watch-items`). Leaving it untouched keeps that behavior and keeps the preference-off behavior byte-for-byte identical (SC-004). A filter that ignores the item has no per-item state to track, so it only needs to announce when the open collection or the preference changes.
- **Corrected during implementation**: the first version of this decision (and of the spec) assumed Show Hidden Games lists hidden and non-hidden games together. The unit test of the filter tree showed it lists only hidden games, so the new filter gained `hidden_only`, the contract table was redone, and the spec was corrected.
- **Verified with a prototype** (run in `gtk-dev` before this plan was written, headless): with the tree above in a `Gtk.FilterListModel(watch_items=True)`, (1) turning the extra filter on listed the hidden game and turning it off removed it again; (2) hiding a game while the extra filter was off removed it from the list at once; (3) hiding a game while it was on kept it; (4) unhiding a game while it was off kept it listed. All four matched the expected results.
- **Alternatives considered**:
  - A `BoolFilter` whose expression is a `ClosureExpression` over the game's `hidden`, `Window.show-hidden`, `Window.collection`, and the preference: one filter instead of two, but it needs a new closure and mixes the item with window properties in one blueprint expression, which is harder to read and which I did not prototype.
  - A single custom filter that reads `game.hidden` itself: a custom filter is not told when a game's property changes, so hiding a game would no longer update the grid until something else re-ran the filter.
  - Changing `CollectionFilter` to let hidden games through: it is a sibling inside the `EveryFilter`, so it cannot override the hidden-games filter next to it.
  - A separate list model for collection views: more state to keep in sync with the sidebar selection for no gain.

## R2. Preference key, binding, and who writes it

- **Decision**: GSettings key `hidden-games-in-collections` (boolean, default `false`). `Window` gets a `hidden_in_collections` property bound one way from the key with `Gio.SettingsBindFlags.GET`; the Preferences switch binds the key two ways through the existing `_bind_switches` set.
- **Rationale**: `_bind_switches` finds each switch by turning the key into an attribute name (`hidden-games-in-collections` becomes `hidden_games_in_collections_switch`), so naming the key this way needs no new binding code. A one-way binding in the window guarantees only Preferences writes the setting. `Reset App` resets every key, so FR-013 needs no extra code. The setting is per build because each build has its own schema.
- **Alternatives considered**: Reading `SETTINGS.get_boolean` inside the filter on each match (no change notification, so toggling would not refresh the grid); storing the preference in the state settings used for window size (those are not reset by `Reset App` and are for window state).

## R3. Label, subtitle, and placement

- **Decision**: An `Adw.SwitchRow` in the General page's Behavior group, titled exactly "Hidden games show in Collections" with `subtitle` "Useful for hiding launchers and tools", next to "Exit After Launching Games" and "Cover Image Launches Game".
- **Rationale**: The texts are the ones requested. The Behavior group already holds the switches that change how browsing and launching behave, and "Cover Image Launches Game" already uses a subtitle the same way.
- **History**: The original request called the text a tooltip and the first version of this feature set `tooltip-text`. The user then said they meant a subtitle, because a tooltip is invisible without hovering and never reaches touch or keyboard users. The feature now uses `subtitle` and no tooltip.
- **Note for review**: The neighboring rows use Title Case ("Exit After Launching Games"); the requested title uses sentence case. This plan keeps the requested text; changing it to "Hidden Games Show in Collections" is a one-word edit if consistency is preferred.

## R4. How to test it

- **Decision**: Add `tests/test_collections.py` in the style of `tests/test_importer.py` (stub the `cartridges` package with a fake `SETTINGS`), registered in `tests/meson.build`. It covers the baseline that has no tests today and the new rule:
  1. Persistence (user story 3): `collections.load()` and `collections.save()` round trip; removed collections are skipped and purged on load; a stored entry missing a field is skipped with one warning; ids of manually added games that no longer exist are dropped while ids of launcher games stay.
  2. Dialog helper: `CollectionEditable.valid` is false for an empty name and true otherwise (names of only spaces count as valid, matching today).
  3. The visibility rules: the same filter tree as `window.blp`, built in Python from the real `CollectionFilter` and `HiddenInCollectionFilter` over a few `Game` objects, checked against [contracts/visibility-rules.md](contracts/visibility-rules.md), including live changes (hide, unhide, switching the preference, opening and closing a collection).
- **Rationale**: These are headless GTK objects, so the test runs in CI with no display. The Python copy of the tree can drift from the blueprint, so the quickstart also has a manual check of the real window.
- **Alternatives considered**: Loading the real `window.ui` in a test (needs the compiled resources, a display, and the whole application); skipping tests because the rule is small (the whole point of the constitution's test rule is that logic like this should not depend on a manual check).

## R5. Translations and docs

- **Decision**: No change to `po/POTFILES.in`: the new strings live in `preferences.blp`, which is already listed. No README change.
- **Rationale**: The extraction picks up the two new strings automatically on the next `cartridges-update-po` run in CI.
