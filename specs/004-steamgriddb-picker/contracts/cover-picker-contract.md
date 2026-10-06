# Contract: Cover Picker UI & Loading Indicators

**Module**: `cartridges.ui.cover_picker`
**Template**: `cartridges/ui/cover_picker.blp`

## 1. Widget Structure Contract

```blueprint
template $CoverPicker: Adw.Dialog {
  title: _("Choose Cover Art");
  content-width: 800;
  content-height: 580;

  child: Adw.ToolbarView {
    [top]
    Adw.HeaderBar {}

    [top]
    Adw.Clamp {
      maximum-size: 500;
      margin-top: 6;
      margin-bottom: 10;
      margin-start: 16;
      margin-end: 16;

      child: SearchEntry search_entry {
        placeholder-text: _("Search SteamGridDB…");
        activate => $_on_search_activated();
        search-changed => $_on_search_changed();
      };
    }

    content: Stack stack {
      transition-type: crossfade;

      StackPage {
        name: "loading";
        child: Adw.Spinner initial_spinner {
          halign: center;
          valign: center;
          width-request: 48;
          height-request: 48;
        };
      }

      StackPage {
        name: "empty";
        child: Adw.StatusPage status_page {
          icon-name: "image-missing-symbolic";
          title: _("No Covers Found");
        };
      }

      StackPage {
        name: "results";
        child: ScrolledWindow {
          hscrollbar-policy: never;

          child: Box {
            orientation: vertical;
            spacing: 16;

            FlowBox flowbox {
              name: "flowbox";
              selection-mode: none;
              max-children-per-line: 4;
              min-children-per-line: 3;
              column-spacing: 16;
              row-spacing: 16;
              margin-top: 16;
              margin-bottom: 16;
              margin-start: 16;
              margin-end: 16;
            }

            Adw.Spinner bottom_spinner {
              halign: center;
              valign: center;
              width-request: 32;
              height-request: 32;
              margin-bottom: 24;
              visible: false;
            }
          };
        };
      }
    };
  };
}
```

## 2. Programmatic Interface Contract

```python
class CoverPicker(Adw.Dialog):
    """Dialog to choose a cover from SteamGridDB."""

    stack: Gtk.Stack
    search_entry: Gtk.SearchEntry
    initial_spinner: Adw.Spinner
    status_page: Adw.StatusPage
    flowbox: Gtk.FlowBox
    bottom_spinner: Adw.Spinner

    def __init__(
        self,
        game: Game | None = None,
        game_name: str = "",
        on_cover_selected: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes dialog, sets search_entry text, and begins cover fetch."""
        ...

    @Gtk.Template.Callback()
    def _on_search_activated(self, entry: Gtk.SearchEntry) -> None:
        """Triggered when Enter is pressed in the search entry.

        Validates non-empty input, increments search generation,
        cancels previous task, clears results, and triggers new fetch.
        """
        ...

    @Gtk.Template.Callback()
    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        """Tracks search text modifications; no immediate API calls."""
        ...

    async def _fetch_covers(self, search_generation: int) -> None:
        """Asynchronously queries SteamGridDB and renders candidates in batches.

        Flow:
        1. stack.set_visible_child_name("loading")
        2. Query game ID and grid options from SteamGridDB for active query
        3. If search_generation != self._search_generation: abort (superseded)
        4. If no grids found: stack.set_visible_child_name("empty")
        5. Render batch 1 (initial candidates) -> stack.set_visible_child_name("results")
        6. If more candidates exist:
             bottom_spinner.set_visible(True)
             Fetch and render subsequent candidates
        7. When all done or on error: bottom_spinner.set_visible(False)
        """
        ...
```
