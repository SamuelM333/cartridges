# Feature Specification: System Color Scheme Synchronization

**Feature Branch**: `feat/006-color-scheme`

**Created**: 2026-10-06
**Updated**: 2026-10-06

**Status**: Complete

**Input**: User description: "keep the system color sync but remove the preference choice toggle"

## User Scenarios & Testing

### User Story 1 - System Color Scheme Synchronization (Priority: P1)

Users expect Cartridges to automatically respect their system-wide dark or light appearance preference (including dynamic day/night transitions) without requiring manual in-app configuration, providing a seamless and native desktop experience.

**Why this priority**: Core user expectation. Modern GNOME applications follow the system desktop theme by default. Eliminating hardcoded theme overrides ensures Cartridges feels right at home on both light and dark desktop setups.

**Independent Test**: Change the desktop environment's appearance setting between Light and Dark mode while Cartridges is closed and while Cartridges is running. Verify that Cartridges starts in and dynamically adapts to the current system appearance.

**Acceptance Scenarios**:

1. **Given** the desktop environment is configured for dark appearance, **When** Cartridges launches, **Then** all windows, dialogs, headers, and game cards present in dark mode from the moment the main window appears.
2. **Given** the desktop environment is configured for light appearance, **When** Cartridges launches, **Then** all windows, dialogs, headers, and game cards present in light mode from the moment the main window appears.
3. **Given** Cartridges is running, **When** the system-wide color scheme switches between light and dark (e.g. manually in GNOME Settings or automatically via scheduled Night Light / day-night timers), **Then** Cartridges updates its visual theme across all active surfaces in real time without requiring a restart.

---

### User Story 2 - Streamlined Preferences Interface (Priority: P2)

Users navigating the Preferences dialog expect a clean, focused settings interface without redundant or non-functional theme toggles.

**Why this priority**: High polish and usability. Removing unnecessary appearance controls simplifies the General preferences tab and avoids confusion between desktop settings and application settings.

**Independent Test**: Open Cartridges Preferences, navigate to the General page, and verify that no appearance or theme toggle group is shown.

**Acceptance Scenarios**:

1. **Given** the user opens the Preferences dialog, **When** viewing the General preferences page, **Then** no color scheme selector or Appearance preferences group is present.
2. **Given** the user interacts with General preferences, **When** reviewing available options, **Then** only functional launcher behaviors (Exit After Launching Games, Cover Image Launches Game, High Quality Images) are displayed.

---

### Edge Cases

- What happens if the host desktop does not report a dark or light preference (e.g. minimal window managers without desktop portals)?
  Cartridges falls back to the standard Libadwaita default color scheme.
- What happens if the system appearance changes while modal dialogs (e.g. Preferences or Add Game) are open?
  All open dialogs and subwindows immediately transition to the new color scheme alongside the main window.
- What happens if an older installation had a custom color-scheme setting stored?
  The application does not enforce manual overrides and respects system theme synchronization unconditionally.

## Requirements

### Functional Requirements

- **FR-001**: System MUST automatically synchronize its visual appearance with the host desktop environment's color scheme (light or dark).
- **FR-002**: System MUST dynamically adapt to runtime changes in the system color scheme without requiring an application restart.
- **FR-003**: System MUST NOT display a manual theme selector or Appearance group in the Preferences dialog.
- **FR-004**: System MUST initialize in the current system-preferred color scheme during startup before presenting the primary window.
- **FR-005**: System MUST ensure all user interface elements (headers, game cards, lists, dialogs, buttons) maintain legible contrast and proper Libadwaita styling in both light and dark appearances.

### Key Entities

- **System Color Scheme**: The active appearance state reported by the operating system desktop environment (light or dark).
- **Application Style**: The visual styling applied to Cartridges UI surfaces, synchronized with the system color scheme.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of application windows and dialogs automatically match the operating system's active color scheme upon launch.
- **SC-002**: Visual styling transitions across all open windows within 100 milliseconds of a system-level color scheme change.
- **SC-003**: 100% of text, icons, and UI elements maintain accessible contrast conforming to WCAG AA standards in both light and dark appearances.
- **SC-004**: General preferences page contains 0 appearance or theme toggle controls.

## Assumptions

- The host desktop environment communicates color scheme preferences via standard desktop portals and Libadwaita style management APIs.
- Setting Libadwaita's color scheme to default (`Adw.ColorScheme.DEFAULT`) provides complete, automated system synchronization without requiring persistent custom settings keys.
- Cartridges does not need custom user-facing overrides once system synchronization is enabled.
