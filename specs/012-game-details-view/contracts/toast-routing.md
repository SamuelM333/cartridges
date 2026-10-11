# Contract: Toast Routing

## `Window.send_toast(title: str, *, undo: Callable[[], Any] | None = None) -> None`

Signature unchanged (`cartridges/ui/window.py`). Every toast in the application goes through it.

| Visible page when called (`navigation_view.props.visible_page`) | Overlay the toast is added to |
|------------------------------------------------------------------|-------------------------------|
| `window.details` (tag `"details"`) | `window.details.toast_overlay` |
| any other page (the library, tag `"games"`) | `window.toast_overlay` (unchanged) |

Unchanged behavior: the title is plain text; with `undo`, the toast gets an "Undo" button, high priority, and an entry in the Undo history used by its button and by `win.undo` (Ctrl+Z).

## `GameDetails` (`cartridges/ui/game-details.blp`, `cartridges/ui/game_details.py`)

| Item | Contract |
|------|----------|
| `toast_overlay: Adw.ToastOverlay` | Template child. The `content:` of the page's `Adw.ToolbarView`, wrapping the existing `ScrolledWindow`. |
| `hiding` signal | Handled by a template callback that calls `toast_overlay.dismiss_all()`. The existing `hidden => $_cancel()` handler is unchanged. |

## Callers (unchanged)

| Caller | Toasts | Where they appear |
|--------|--------|-------------------|
| `games.play` | "Launched {}" | The view Play was pressed in (FR-009, FR-013) |
| `games.hide`, `games.remove` from details | "{} hidden", "{} removed" with Undo | The library, because the details page pops first (FR-012) |
| `games.hide`, `unhide`, `remove` from the library | Same, with Undo | The library |
| `GameEditable._save` | "{} could not be saved ..." | The details view, where Apply was pressed |
| `collections.remove`, `preferences`, `application` | Their existing messages | The view showing at the time (FR-010) |

## Requirement mapping

| Requirement | Satisfied by |
|-------------|--------------|
| FR-009 | Details overlay plus the routing table above |
| FR-010 | One overlay per page; each toast is added to exactly one |
| FR-011 | `dismiss_all()` on `hiding` |
| FR-012 | `visible_page` switches when the pop happens (research R1) |
| FR-013 | The library row of the routing table is the current behavior |
