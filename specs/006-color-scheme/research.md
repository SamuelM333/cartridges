# Phase 0 Research: System Color Scheme Synchronization

## Architectural Decisions

### Decision 1: Automatic System Theme Synchronization via `Adw.ColorScheme.DEFAULT`
- **Decision**: Configure `Adw.StyleManager` to use `Adw.ColorScheme.DEFAULT` during application startup, replacing the previous hardcoded `Adw.ColorScheme.PREFER_DARK`.
- **Mechanism**:
  - In `cartridges/application.py`, within `Application.do_startup()`:
    ```python
    self.props.style_manager.props.color_scheme = Adw.ColorScheme.DEFAULT
    ```
- **Rationale**:
  - `Adw.ColorScheme.DEFAULT` is Libadwaita's standard native mode. It connects directly to the Freedesktop Settings Portal (`org.freedesktop.portal.Settings` `color-scheme` key) and the host GNOME desktop settings.
  - When the system switches between Light and Dark mode (manual user toggle or automated day/night schedules), Libadwaita automatically updates all window surfaces, CSS variables, and widget styling instantaneously across the entire process.
  - Cartridges previously overrode this by explicitly forcing `PREFER_DARK`. Reverting to `DEFAULT` restores seamless, native GNOME desktop integration.
- **Alternatives Considered**:
  - Leaving `PREFER_DARK` hardcoded: Fails user intent to have light theme support on light desktop environments.
  - Custom portal dbus listener: Unnecessary duplicate effort; Libadwaita's `AdwStyleManager` already provides this out of the box.

### Decision 2: Removal of Preferences Toggle Controls
- **Decision**: Do not display an Appearance group or color scheme toggle group in `cartridges/ui/preferences.blp` or controller logic in `cartridges/ui/preferences.py`.
- **Rationale**:
  - Streamlines the General preferences page, keeping it focused on game launching and library management behaviors.
  - Prevents application-level preference desynchronization from the host desktop.
  - Follows GNOME HIG recommendations for applications that naturally follow the desktop appearance without requiring manual in-app overrides.
- **Alternatives Considered**:
  - Retaining toggles: Directly contradicts the revised user requirement to remove the preference choice toggle.

### Decision 3: Removal of Custom GSettings Persistence Key
- **Decision**: Remove the `color-scheme` key from `data/page.samuelm333.Cartridges.gschema.xml.in`.
- **Rationale**:
  - Because theme state is entirely governed by the host desktop environment via `Adw.ColorScheme.DEFAULT`, no application-local persistence or GSettings schema key is needed.
  - Eliminates unnecessary schema bloat, settings bindings, and change listeners.
- **Alternatives Considered**:
  - Keeping an unused GSettings key: Creates dead schema definitions and confusing configuration keys.
