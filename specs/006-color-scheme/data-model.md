# Data Model: System Color Scheme Synchronization

## Entities

### SystemThemeState

Represents the active operating system appearance state retrieved via Libadwaita's `Adw.StyleManager`.

| Property | Type | Source | Possible Values | Behavior |
|---|---|---|---|---|
| `dark` | `bool` | `Adw.StyleManager.get_default().get_dark()` | `True`, `False` | True if the host desktop is in dark mode; False if in light mode |
| `color_scheme` | `Adw.ColorScheme` | `Adw.StyleManager.get_default().get_color_scheme()` | `Adw.ColorScheme.DEFAULT` | Configured to `DEFAULT` so the style manager delegates appearance to the host environment |

#### Value Semantics

- **`Adw.ColorScheme.DEFAULT`**: Follows host operating system appearance preference automatically. If the desktop preference toggles between dark and light, Cartridges adapts immediately.
- **Dynamic Updates**: Libadwaita subscribes to the `org.freedesktop.portal.Settings` portal (`color-scheme` key) and the local desktop settings, notifying all widgets upon transition.

---

### Preferences UI Structure

The General page inside `cartridges/ui/preferences.blp` remains focused on core launcher behaviors and image caching, without an Appearance group:

```text
Adw.PreferencesDialog
└── Adw.PreferencesPage ("general_page")
    ├── Adw.PreferencesGroup ("behavior_group")
    │   ├── Adw.SwitchRow ("exit_after_launch_switch")
    │   └── Adw.SwitchRow ("cover_launches_game_switch")
    ├── Adw.PreferencesGroup ("images_group")
    │   └── Adw.SwitchRow ("high_quality_images_switch")
    └── Adw.PreferencesGroup ("danger_zone_group")
        ├── Adw.ButtonRow ("remove_all_games_button_row")
        └── Adw.ButtonRow ("reset_button_row")
```

---

## State Flow

```
+------------------------------------------------+
| Host Desktop Theme Change                      |
| (GNOME Settings / Day-Night Schedule / Portal) |
+-----------------------+------------------------+
                        |
                        v
+------------------------------------------------+
| Adw.StyleManager (Process Singleton)           |
| Receives portal notification                   |
+-----------------------+------------------------+
                        |
                        v
+------------------------------------------------+
| Cartridges Windows, Views, & Dialogs           |
| Instantly re-render with updated CSS variables |
+------------------------------------------------+
```
