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
    ) -> None: ...

    async def _fetch_covers(self) -> None:
        """Asynchronously queries SteamGridDB and renders candidates in batches.

        Flow:
        1. stack.set_visible_child_name("loading")
        2. Query game ID and grid options from SteamGridDB
        3. If no grids found: stack.set_visible_child_name("empty")
        4. Render batch 1 (initial candidates) -> stack.set_visible_child_name("results")
        5. If more candidates exist:
             bottom_spinner.set_visible(True)
             Fetch and render subsequent candidates
        6. When all done or on error: bottom_spinner.set_visible(False)
        """
        ...
```
