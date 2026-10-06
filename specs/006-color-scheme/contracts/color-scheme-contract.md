# Interface Contract: System Color Scheme Synchronization

## 1. Application Startup Contract

**Target File**: `cartridges/application.py`

### Startup Initialization
In `Application.do_startup()`:
- `self.props.style_manager.props.color_scheme` MUST be set to `Adw.ColorScheme.DEFAULT` (or left at Libadwaita's default).
- The previous hardcoded `Adw.ColorScheme.PREFER_DARK` MUST NOT be set.
- No GSettings listeners or custom color scheme handlers are attached to `SETTINGS`.

### Invariants
- `Adw.StyleManager` operates in `DEFAULT` mode across the entire application lifecycle.
- Runtime changes from the Freedesktop Settings portal (`color-scheme`) propagate automatically to all windows and views.

---

## 2. Blueprint UI Template Contract

**Target File**: `cartridges/ui/preferences.blp`

### Preferences Dialog Hierarchy
- `general_page` MUST NOT contain an `appearance_group` or `color_scheme_group`.
- The first group under `general_page` is `behavior_group`.
- Clean hierarchy:
  ```blueprint
  Adw.PreferencesPage general_page {
    name: "general";
    title: _("General");
    icon-name: "user-home-symbolic";

    Adw.PreferencesGroup behavior_group {
      title: _("Behavior");
      ...
    }
  }
  ```

---

## 3. Preferences Controller Contract

**Target File**: `cartridges/ui/preferences.py`

### Controller Children and Bindings
- `CartridgesPreferences` MUST NOT declare `@Gtk.Template.Child() color_scheme_group`.
- `CartridgesPreferences.__init__()` MUST NOT call any color scheme binding helpers.
- Only functional switches and launcher settings are bound.

---

## 4. GSettings Schema Contract

**Target File**: `data/page.samuelm333.Cartridges.gschema.xml.in`

### Schema Keys
- The schema `page.samuelm333.Cartridges` MUST NOT define a `color-scheme` key.
- No custom theme configuration persists in user settings.
