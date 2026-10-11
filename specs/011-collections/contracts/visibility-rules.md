# Contract: Which Games the Grid Lists

The main grid lists a game when **all** of these hold:

1. The game is not removed and not blacklisted (unchanged, applied by the games model).
2. If a collection is open, the game is in it.
3. The search text, if any, matches the game's name or developer.
4. **Hidden rule**:
   - **Show Hidden Games off**: the game is not hidden, **or** (a collection is open **and** the preference is on).
   - **Show Hidden Games on**: the game is hidden. This view lists only hidden games, with or without a collection, and the preference has no effect on it.

## Rule 4 as a table

Three games pass rules 1 to 3 in a collection view: `visible` (not hidden), `hidden_in` (hidden, in the collection). `hidden_out` (hidden, not in the collection) passes only outside a collection.

| View | Show Hidden Games | Preference | Games listed |
|------|-------------------|------------|--------------|
| All Games or a source | off | off | `visible` |
| All Games or a source | off | on | `visible` |
| All Games or a source | on | off | `hidden_in`, `hidden_out` |
| All Games or a source | on | on | `hidden_in`, `hidden_out` |
| A collection | off | off | `visible` |
| A collection | off | on | `hidden_in`, `visible` (new) |
| A collection | on | off | `hidden_in` |
| A collection | on | on | `hidden_in` |

With the preference off, every row is today's behavior (SC-004). The only row that changes is "A collection, Show Hidden Games off, preference on".

## Live behavior

The grid updates without a restart or a reselect when: a game is hidden or unhidden, Show Hidden Games is toggled, the preference is toggled, or another collection (or the main list) is opened.

## Unchanged

Hide and Unhide stay available per the game's own state, the toasts and Undo are the same, hiding a game never removes it from its collections, and empty views show the same status pages (a collection that lists nothing shows "No Games in {name}").
