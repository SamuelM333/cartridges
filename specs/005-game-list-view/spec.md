# Feature Specification: Main Game List View and Cover Interactions

**Feature Branch**: `feat/005-game-list-view`

**Created**: 2026-10-04

**Status**: Draft

**Input**: User description: "main game list view spec. copy the existing design to the spec. recover previous buttons showing on hover design from cartridges-main, where three dots opens settings, play launches the game and I icon opens the info, with a toggle for these last two in settings 'Cover image launches game' (as already implemented)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse and Launch Games from Grid (Priority: P1)

As a player with a library of games, I want to browse my game collection in a visually rich cover grid and launch games directly using hover action buttons or cover interaction, so that I can quickly jump into playing my games.

**Why this priority**: Browsing and launching games is the primary core purpose of the application. Without a functional, responsive game list view with intuitive launch controls, the application cannot serve its basic function.

**Independent Test**: Can be verified by viewing the library grid with games populated, hovering over a game card to see action buttons appear, and clicking the launch button (or cover) to launch the game executable.

**Acceptance Scenarios**:

1. **Given** the library view is active with games, **When** the user moves the pointer over a game card, **Then** an action button appears in the top-left corner and a menu button (three dots) appears in the top-right corner with a smooth reveal transition.
2. **Given** the setting "Cover image launches game" is disabled (default), **When** the user hovers over a game cover, **Then** the top-left button displays a Play icon (`media-playback-start-symbolic`).
3. **Given** the setting "Cover image launches game" is disabled (default), **When** the user clicks the Play icon on hover, **Then** the game launches immediately and a dismissable toast notification appears with the localized message "Launched <game name>".
4. **Given** the setting "Cover image launches game" is disabled (default), **When** the user clicks the cover image directly (or activates the focused item with keyboard/gamepad), **Then** the game details view opens.

---

### User Story 2 - Invert Cover and Button Behavior via Settings Toggle (Priority: P1)

As a player who prefers launching games with a single click on the cover, I want to configure the cover image to launch games while retaining quick access to game details via an Info button on hover, so that the interface matches my preferred launching style.

**Why this priority**: Users have different habits; some prefer cover clicks to inspect details while others prefer cover clicks for immediate launching. Providing the toggle with consistent icon feedback ensures an optimal user experience.

**Independent Test**: Can be verified by toggling "Cover image launches game" in Preferences, observing that the hover button icon swaps to an Info ("I") icon, and confirming that clicking the cover launches the game while clicking the Info button opens details.

**Acceptance Scenarios**:

1. **Given** the setting "Cover image launches game" is enabled, **When** the user views the game grid, **Then** the top-left hover button displays an Info icon (`help-about-symbolic`).
2. **Given** the setting "Cover image launches game" is enabled, **When** the user clicks the Info button on hover, **Then** the game details view opens.
3. **Given** the setting "Cover image launches game" is enabled, **When** the user clicks the cover image directly, **Then** the game launches immediately and a dismissable toast notification appears with the localized message "Launched <game name>".
4. **Given** the user changes the "Cover image launches game" toggle in Preferences, **When** returning to the library grid, **Then** all game cards reflect the updated hover icon and click interaction without requiring an application restart.

---

### User Story 3 - Access Game Context Menu via Hover Three-Dots Button (Priority: P2)

As a player organizing my library, I want to access game management actions (Edit, Hide/Unhide, Remove, and Collection assignment) directly from a three-dots menu button on hover, so that I can manage games without navigating away from the list view.

**Why this priority**: Quick contextual actions streamline library maintenance and organization directly from the browsing view.

**Independent Test**: Can be verified by hovering over a game card, clicking the three-dots button in the top-right corner, and verifying that the options popover opens with Edit, Hide/Unhide, Remove, and Collections actions.

**Acceptance Scenarios**:

1. **Given** the pointer hovers over a game card, **When** the three-dots button in the top-right corner appears and is clicked, **Then** a contextual popover menu opens containing game actions.
2. **Given** the contextual menu is open, **When** the pointer moves away from the card, **Then** the menu and its trigger button remain visible until the popover is closed or an action is chosen.
3. **Given** a visible game, **When** the user selects "Hide" from the menu, **Then** the game is hidden from the primary list and a confirmation toast with an Undo action appears.
4. **Given** the user selects "Edit" from the menu, **When** triggered, **Then** the application navigates to the game details view in editing mode.
5. **Given** the user selects "Remove" from the menu, **When** triggered, **Then** the game is removed from the library and a confirmation toast with an Undo action appears.

---

### User Story 4 - Empty States and Library Navigation (Priority: P3)

As a player navigating different views, searching, or filtering, I want clear feedback when a view contains no games (such as empty search results, empty collections, or empty hidden list), so that I understand why no games are shown and know what action to take next.

**Why this priority**: Clear status pages prevent confusion when lists are filtered or empty, ensuring consistent adherence to GNOME Human Interface Guidelines.

**Independent Test**: Can be verified by searching for a nonexistent game name, viewing an empty collection, viewing an empty hidden games list, or viewing a fresh library with zero games.

**Acceptance Scenarios**:

1. **Given** a search query matches zero games, **When** displayed, **Then** a "No Games Found" status page is shown with an instruction to try a different search.
2. **Given** the user toggles "Show Hidden Games" with no hidden games present, **When** displayed, **Then** a "No Hidden Games" status page is shown.
3. **Given** the user selects an empty collection, **When** displayed, **Then** a "No Games in {Collection}" status page is shown.
4. **Given** the library contains no games at all, **When** displayed, **Then** a "No Games" status page is shown with guidance to add games.

---

### Edge Cases

- Pointer hovering near card boundaries: Action buttons must not flicker when the cursor transitions over button borders or child overlays.
- Rapid hover enter/leave: Animations and revealer states must handle fast mouse movements gracefully without stuck visual artifacts.
- Keyboard navigation: Focusing a card via Tab/Arrow keys must reveal accessible visual focus indicators and allow triggering primary activation (Enter/Space) and secondary actions.
- Gamepad navigation: When a gamepad is connected, directional navigation highlights the focused game card, and button mapping (e.g. A button to activate, X/Y for secondary actions) operates according to user settings.
- Missing cover artwork: When a game has no custom cover image, a standard fallback placeholder cover is displayed with the title visible, and hover controls remain fully functional.
- Long game titles: Title labels under the cover must be ellipsized cleanly to preserve the grid alignment across columns.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST present games in an adaptive grid view conforming to GNOME Human Interface Guidelines and Libadwaita layout standards.
- **FR-002**: System MUST display an overlay on each game card containing circular action buttons that appear when the pointer enters the card and disappear when the pointer leaves.
- **FR-003**: System MUST position a primary action button at the top-left of the game card overlay and a secondary contextual menu button (three dots) at the top-right of the game card overlay.
- **FR-004**: System MUST keep the top-right three-dots menu button and overlay visible as long as its associated popover menu remains open, regardless of pointer position.
- **FR-005**: When the "Cover image launches game" setting is disabled (default):
  - The top-left hover button MUST display the Play icon (`media-playback-start-symbolic`).
  - Clicking the top-left hover button MUST launch the game executable.
  - Clicking the cover image MUST open the game details view.
- **FR-006**: When the "Cover image launches game" setting is enabled:
  - The top-left hover button MUST display the Info icon (`help-about-symbolic`).
  - Clicking the top-left hover button MUST open the game details view.
  - Clicking the cover image MUST launch the game executable.
- **FR-007**: System MUST provide a user preference toggle labeled "Cover Image Launches Game" with the subtitle "Swaps the behavior of the cover image and the play button" in the application Preferences dialog under the general Behavior group.
- **FR-008**: System MUST dynamically update all rendered game cards when the "Cover image launches game" preference is modified without requiring an application restart.
- **FR-009**: The top-right three-dots menu MUST provide access to Edit, Hide/Unhide, Remove, and Collection assignment actions.
- **FR-010**: System MUST display dedicated empty status pages with informative titles, descriptions, and symbolic icons for empty search results, empty collections, empty hidden games list, and an empty library.
- **FR-011**: System MUST support keyboard and gamepad navigation across the game list grid, maintaining clear focus outlines and accessible action triggers.
- **FR-012**: When a game launch is initiated from any grid control (hover Play button, cover click, or keyboard/gamepad activation), the system MUST display a dismissable in-app toast notification stating "Launched <game name>".
- **FR-013**: The toast notification message MUST be marked for gettext localization with interpolation placeholders to enable grammatically accurate translations across all supported languages.

### Key Entities

- **Game Card**: The visual representation of a game in the library grid, consisting of a cover image, overlay controls (top-left action button, top-right menu button), and a title label.
- **Cover Overlay**: A transparent overlay layer positioned over the cover picture that hosts the revealer buttons triggered on pointer motion.
- **Hover Action Button**: A circular button in the top-left corner whose icon and action (Play vs. Info) correspond to the inverse of the cover click behavior.
- **Contextual Menu Button**: A circular button in the top-right corner displaying three dots (`view-more-symbolic`) that opens the game management popover.
- **Launch Toast Notification**: A transient, dismissable visual feedback toast that informs the user that the requested game launch command has been executed.
- **Preferences Configuration**: Persistent user settings including the boolean preference key `cover-launches-game`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Hover action buttons appear and reach full visibility within 250 milliseconds of pointer entry.
- **SC-002**: Launching a game from either the hover Play button or the cover image (when configured) initiates the launch sequence within 200 milliseconds of user click.
- **SC-003**: Changing the "Cover Image Launches Game" setting immediately swaps the icons and actions of all displayed game cards in under 100 milliseconds.
- **SC-004**: 100% of game cards in any filtered view or collection display the correct hover controls and title without layout breakage or button overlap.
- **SC-005**: All interactions and empty state pages comply with GNOME Human Interface Guidelines and pass accessibility validation with keyboard navigation.
- **SC-006**: The dismissable "Launched <game name>" toast appears within 100 milliseconds of launch activation and renders the translated string with the exact game title.

## Assumptions

- The persistent setting `cover-launches-game` is already defined in the GSettings schema and exposed in the preferences dialog.
- The game launching subsystem and details navigation view are already established components within the application architecture.
- Circular buttons on the card overlay use standard Libadwaita styling (`circular`, `osd`) with high contrast and backdrop blur for readability against diverse game cover images.
- Gamepad navigation monitors controller events and maps standard controller button presses to the same logical actions as mouse and keyboard navigation.
- An in-app toast overlay (`AdwToastOverlay`) is available in the main window hierarchy to present dismissable launch notifications.
