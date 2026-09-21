# Feature Specification: Flatpak Game Source, SteamGridDB Cover Art Integration, and Preferences Menu

**Feature Branch**: `002-port-legacy-features`

**Created**: 2026-09-21

**Status**: Draft

**Input**: User description: "draft a new feature. let's review the differences and missing features in main and implement them in rewrite. there's a separate folder for main available, let's keep it read only /var/home/samuel/Projects/cartridges-main. Scope decisions: focus on Flatpak source and SteamGridDB; defer Bottles, RetroArch, and Search Provider to future specs. SteamGridDB authenticated via user-supplied API key. Preferences menu in the settings panel is a P0 prerequisite."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover and Import Flatpak Games (Priority: P1)

As a Linux desktop gamer, I want Cartridges to automatically scan for installed Flatpak games and applications and add them to my library, so that all my sandboxed games can be launched easily alongside my Steam, Heroic, and Lutris games.

**Why this priority**: Flatpak is the primary package distribution format on modern Linux gaming desktops (such as SteamOS, Fedora Silverblue, and Bazzite).

**Independent Test**: Install a Flatpak game (or provide a mock Flatpak installation descriptor). Trigger library import in Cartridges and verify that the game is detected with its desktop title, icon/cover, and executable Flatpak launch command.

**Acceptance Scenarios**:

1. **Given** installed system or user Flatpak gaming applications, **When** library discovery runs, **Then** all gaming Flatpaks appear in Cartridges with proper titles and metadata.
2. **Given** an imported Flatpak game, **When** the user clicks "Play", **Then** the application launches correctly via the host's Flatpak runner or desktop portal.
3. **Given** non-game utility Flatpaks or Cartridges itself, **When** scanning occurs, **Then** non-game tools and launchers are filtered out.

---

### User Story 2 - Fetch and Choose Cover Art from SteamGridDB (Priority: P1)

As a user with games lacking cover art or who wants custom alternative artwork, I want to fetch cover art options directly from SteamGridDB using my personal API key, so that I can browse and select high-resolution covers for any game.

**Why this priority**: Consistent, visually striking grid artwork is essential for an enjoyable launcher experience.

**Independent Test**: Enter a valid SteamGridDB API key in settings. On a game with missing or placeholder artwork, trigger the cover search dialog, browse the returned cover options, select one, and confirm that the image downloads and updates the game's displayed cover.

**Acceptance Scenarios**:

1. **Given** a valid SteamGridDB API key configured, **When** the user opens the cover picker for a game, **Then** matching cover art results (vertical/grid artwork) from SteamGridDB are retrieved and presented.
2. **Given** a selected cover image, **When** confirmed, **Then** the image is downloaded asynchronously, stored in the local cache, and immediately reflected in the game details and grid.
3. **Given** an invalid or empty SteamGridDB API key, **When** a user attempts to search for covers, **Then** a clear, friendly error prompt explains how to obtain and enter a free API key.

---

### User Story 3 - Configure Application Preferences and SteamGridDB Key (Priority: P0)

As a user, I want a central Preferences dialog accessible from the main menu, so that I can configure application behavior (such as exit after launch, cover launches game, automatic imports) and input my SteamGridDB API key.

**Why this priority**: General settings are a foundational part of the user experience and must be restored to allow configuring Flatpak and SteamGridDB options.

**Independent Test**: Click on the main menu button, select "Preferences", and verify that the Preferences dialog opens. Change settings (such as "Exit after launch" or inputting a mock SteamGridDB API key) and verify they are stored and reflected immediately.

**Acceptance Scenarios**:

1. **Given** the application is running, **When** the user clicks the open-menu button, **Then** a "Preferences" option is displayed in the menu list.
2. **Given** the Preferences menu option is selected, **When** clicked, **Then** a Libadwaita-styled Preferences Dialog opens containing groups for General, Import, and SteamGridDB settings.
3. **Given** options inside the Preferences Dialog (such as "Exit after launch" or "Auto import"), **When** toggled, **Then** the corresponding configuration key updates instantly.
4. **Given** a SteamGridDB API key entered in the text field within the SteamGridDB settings group, **When** changed, **Then** the key is stored instantly and sensitive dependent options (like enabling SteamGridDB) are unlocked or locked accordingly.

---

### User Story 4 - Application Behavior Customization (Priority: P1)

As a user of Cartridges, I want to toggle whether the application exits after launching a game and whether clicking a game's cover image launches the game directly (reversing the standard details dialog behavior), so that I can tailor the application's flow to my personal play style.

**Why this priority**: Customizing how the launcher reacts to launching games is a primary convenience feature that directly affects the core application navigation loop.

**Independent Test**: Enable the behavior settings in the Preferences dialog. Click a cover in the library grid to verify if details are shown or if the game launches directly. Launch a game and verify if Cartridges terminates automatically based on the exit toggle.

**Acceptance Scenarios**:

1. **Given** "Exit After Launching Games" is enabled, **When** a game is successfully launched, **Then** Cartridges must close its window and terminate immediately.
2. **Given** "Exit After Launching Games" is disabled, **When** a game is launched, **Then** Cartridges must remain running in the background.
3. **Given** "Cover Image Launches Game" is enabled, **When** a game's cover in the library grid is clicked, **Then** the game must launch immediately without opening the details view.
4. **Given** "Cover Image Launches Game" is enabled, **When** the small play button is clicked, **Then** the details view must open.
5. **Given** "Cover Image Launches Game" is disabled, **When** a game's cover is clicked, **Then** the details view must open.

---

### User Story 5 - Image Quality Control (Priority: P2)

As a user with storage constraints or high-end displays, I want to toggle whether game covers are saved in high quality or losslessly, so that I can choose between high-fidelity visual aesthetics and storage optimization.

**Why this priority**: Custom cover quality preferences let users manage local storage utilization on portable devices like Steam Deck while maintaining sharp visuals on high-DPI desktop monitors.

**Independent Test**: Toggle "High Quality Images" in settings, import new games or manually update game cover art, and verify the file format and size of saved image files in the local cache.

**Acceptance Scenarios**:

1. **Given** "High Quality Images" is enabled, **When** cover images are fetched and saved, **Then** they are stored in a lossless high-resolution format in the cache.
2. **Given** "High Quality Images" is disabled, **When** cover images are saved, **Then** they are compressed/optimized to minimize local storage usage.

---

### User Story 6 - Settings and Library Safety Control (Danger Zone) (Priority: P2)

As a user wishing to reset their setup or clear private data, I want options to safely remove all imported games and completely reset the application configuration to its defaults from the Preferences screen, so that I do not need to manually delete local folders or settings keys.

**Why this priority**: Provides users with complete, self-contained control over their data, preventing the need for manual filesystem cleanup.

**Independent Test**: Populate the library with several imported games and custom configurations. Click "Remove All Games" and confirm. Verify the library is empty. Click "Reset App" and confirm. Verify all options are restored to factory defaults.

**Acceptance Scenarios**:

1. **Given** imported games exist in the library, **When** the user clicks "Remove All Games" in the Danger Zone and confirms, **Then** all imported and manually added games are cleared from the library database.
2. **Given** custom application configuration has been applied, **When** the user clicks "Reset App" in the Danger Zone and confirms, **Then** all configurations and persistent state keys are restored to their initial installation defaults.

---

### User Story 7 - Modular Source Settings (Priority: P1)

As a multi-platform gamer, I want to configure independent scanning toggles, folder paths, and import preferences for each of my game sources (Steam, Lutris, Heroic, Itch, Legendary, Desktop, and Flatpak) under a unified Import panel, so that I have fine-grained control over library population.

**Why this priority**: Library customization is a fundamental feature of a multi-source launcher; players must be able to specify path structures and disable unused platforms.

**Independent Test**: Navigate to the Import tab in Preferences. Enable or disable individual sources, change their folder paths, and toggle sub-options. Run library sync and confirm that only the chosen sources and sub-categories are queried.

**Acceptance Scenarios**:

1. **Given** a specific game source is disabled, **When** a library sync is executed, **Then** no scanning or queries are directed to that source.
2. **Given** a custom library installation directory is specified for a source, **When** scanning runs, **Then** the application scans the provided path instead of the default location.
3. **Given** import sub-toggles (such as Heroic Epic, GOG, Amazon, Sideload, or Lutris Steam, Flatpak) are set, **When** import runs, **Then** only games matching the active sub-toggles are imported.

---

### User Story 8 - Comprehensive SteamGridDB Configuration (Priority: P1)

As a user of SteamGridDB, I want options to manage my SteamGridDB API key, toggle the search feature, prefer SteamGridDB covers over official ones, prefer animated covers, and trigger a manual bulk cover update, so that my library grid looks spectacular.

**Why this priority**: SteamGridDB is the primary source of metadata and artwork, and users must have full control over query criteria and manual refreshing.

**Independent Test**: Enter a SteamGridDB API key, toggle active parameters (such as Prefer Animated Images), click "Update Covers", and check that matching animated images are retrieved and populated for the library.

**Acceptance Scenarios**:

1. **Given** SteamGridDB is disabled, **When** importing games, **Then** Cartridges does not execute network queries to SteamGridDB.
2. **Given** SteamGridDB is enabled and "Prefer Animated Images" is checked, **When** fetching cover choices, **Then** animated APNG or GIF covers are selected and displayed where available.
3. **Given** "Update Covers" is triggered, **When** the process runs, **Then** Cartridges queries SteamGridDB asynchronously for all games in the library and updates their cache, showing progress in the UI.

### Edge Cases

- **Flatpak Sandbox Portal Limitations**: When Cartridges is itself running inside a Flatpak sandbox, launching another Flatpak application cannot be done directly via subprocess `flatpak run`; it must be executed through the host command execution portal (`org.freedesktop.portal.Flatpak` / `HostCommand`).
- **Network Outages or API Rate Limiting**: If SteamGridDB is unreachable, slow, or returns rate-limit responses, the UI must remain responsive, display non-blocking error indicators, and allow manual cancellation.
- **Games with Ambiguous or Missing Match Names**: If an imported Flatpak game has an unusual internal name (e.g., reverse-DNS ID like `net.supertuxkart.SuperTuxKart`), the search query should fallback to the user-facing application name to maximize match quality on SteamGridDB.
- **Read-Only Legacy Reference**: The legacy repository at `/var/home/samuel/Projects/cartridges-main` must remain completely unmodified and read-only.
- **Invalid Directory Selection in Preferences**: If a user selects an invalid directory for any source path, the interface must display a clear warning popover on that row and prevent saving the invalid value, without crashing the application.
- **Empty or Whitespace API Keys**: Entering a blank or whitespaced API key should disable all SteamGridDB features and mark the configuration as inactive.
- **Accidental Deletions**: In the Danger Zone, triggers like "Remove All Games" or "Reset App" must show a clear confirmation modal before deleting any data or restoring defaults.
- **Offline Mode during Bulk Updates**: If a bulk cover update is triggered while the machine is offline, the update must fail gracefully without hanging, alerting the user to check their connection.
- **Source Paths with Symlinks or Invalid Permissions**: If a folder path is set to an unreadable directory, the application must display a validation warning and ignore the path without crashing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement a modular `FlatpakSource` subclass under `cartridges/sources/` complying with the project's source interface.
- **FR-002**: System MUST identify installed Flatpak applications from standard system (`/var/lib/flatpak/app`) and user (`~/.local/share/flatpak/app`) export paths.
- **FR-003**: System MUST filter out known utilities, base dependencies, runtime SDKs, and launcher frontends from the Flatpak import list.
- **FR-004**: System MUST provide a secure configuration mechanism inside the Preferences dialog to store and persist a user-supplied SteamGridDB API key, enabling or disabling SteamGridDB cover integration dynamically based on the presence of a key.
- **FR-005**: System MUST query the SteamGridDB API asynchronously for game cover artwork without blocking the main GTK application loop.
- **FR-006**: System MUST present a cover selection dialog or view displaying available SteamGridDB thumbnail options for a selected game.
- **FR-007**: System MUST download selected covers and save them into the application's local cover cache directory conforming to XDG standards.
- **FR-008**: System MUST implement a central general Preferences dialog based on `Adw.PreferencesDialog` and GNOME Blueprint as a P0 requirement, integrating configurations for general settings, source-specific options (such as Flatpak), and SteamGridDB settings. Other legacy features (Bottles source, RetroArch source, and GNOME Search Provider) remain deferred to future specifications.
- **FR-009**: All new modules, controllers, and data structures MUST pass Pyright in `strict` type-checking mode and comply with Ruff linting rules.
- **FR-010**: All UI components (such as cover picker, preferences dialog, or API key entry) MUST be declared in GNOME Blueprint (`.blp`) format.
- **FR-011**: System MUST add a "Preferences" menu item to the main window's header bar menu that triggers the presentation of the Preferences dialog.
- **FR-012**: System MUST bind all controls inside the Preferences dialog (switches, entry rows, file/folder pickers) directly to their corresponding configuration keys, ensuring modifications are saved immediately.
- **FR-013**: System MUST validate user-picked directories (such as Flatpak library paths) using appropriate checks and display a non-blocking error/warning popover if the directory is invalid, without crashing.
- **FR-014**: System MUST provide toggles for "Exit After Launching Games" and "Cover Image Launches Game" under a Behavior group.
- **FR-015**: System MUST swap game click behavior when "Cover Image Launches Game" is enabled, so that clicking the cover launches the game and clicking the play button opens the details.
- **FR-016**: System MUST provide a toggle for "High Quality Images" under an Images group.
- **FR-017**: System MUST provide destructive actions for "Remove All Games" and "Reset App" under a separate Danger Zone group, each requiring user confirmation via a modal before execution.
- **FR-018**: System MUST provide configuration settings for all supported sources (Steam, Lutris, Heroic, Itch, Legendary, Desktop, Flatpak) including path selectors and platform-specific sub-toggles in an Import page.
- **FR-019**: System MUST provide SteamGridDB settings: API key input row, "Use SteamGridDB" toggle, "Prefer Over Official Images" toggle, and "Prefer Animated Images" toggle.
- **FR-020**: System MUST provide a manual "Update Covers" action row with an asynchronous progress spinner inside the SteamGridDB preferences group.
- **FR-021**: System MUST persist all configurations in GSettings schemas instantly upon toggle or input change.
- **FR-022**: System MUST reference the legacy implementation's design, styling, widgets, and layout patterns (specifically matching `data/gtk/preferences.blp` in the `cartridges-main` reference) as closely as possible, and MUST NOT introduce any new, custom, or divergent UI/UX layout concepts.
- **FR-023**: System MUST bundle and register a symbolic SVG icon for Flatpak (`flatpak-symbolic.svg`) to render its logo in the application's sidebar and lists.
- **FR-024**: System MUST filter out and ignore Flatpak-exported application entries inside the Desktop source scanner (by checking for the presence of the `X-Flatpak` key in desktop entries) to completely prevent duplicated items in the game grid.

### Key Entities

- **Flatpak Game Source**: Source provider responsible for querying host Flatpak installations, inspecting desktop entries, and generating launchable game models.
- **SteamGridDB Client**: Network service handling authenticated requests, rate limiting, and response parsing for SteamGridDB game searches and grid image queries.
- **Cover Candidate**: Data model representing an image candidate retrieved from SteamGridDB, including thumbnail URL, full image URL, author attribution, and dimensions.
- **Preferences Dialog**: UI controller component using Gtk.Template with a Blueprint definition, responsible for rendering settings pages and groups, binding widgets to GSettings, and providing validation for folder selections.
- **Danger Zone Manager**: Component responsible for safely executing database wiping (Remove All Games) and setting restoration (Reset App).
- **SteamGridDB Fetcher**: Asynchronous background worker responsible for bulk updating library artwork without blocking the main GTK application loop.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of installed game Flatpaks on test environments are correctly detected and added to the library without manual intervention.
- **SC-002**: 100% of game launches from the Flatpak source succeed on both native and Flatpak installations of Cartridges.
- **SC-003**: SteamGridDB search returns cover options within 3 seconds under normal network conditions.
- **SC-004**: 100% of new code passes Pyright in `strict` mode with zero type errors and zero Ruff lint errors.
- **SC-005**: Zero regressions to existing source importers (Steam, Heroic, Lutris, Itch, Legendary) or existing cover management.
- **SC-006**: Opening the Preferences dialog takes less than 200ms and consumes minimal additional system memory.
- **SC-007**: 100% of setting changes made inside the Preferences dialog are persisted instantly without manual saving or application restart.
- **SC-008**: All configuration changes are saved and persisted instantly (under 50ms) to the persistent database/configuration store.
- **SC-009**: 100% of destructive operations require explicit confirmation and finish in less than 1 second once confirmed.
- **SC-010**: Manual cover art updates run asynchronously in the background, keeping the user interface completely responsive with a stable 60 FPS framerate.
- **SC-011**: All source files, specifications, and checklist documents have zero lint, formatting, or style errors.

## Assumptions

- **A-001**: Users configure their SteamGridDB API key directly inside the new Preferences dialog.
- **A-002**: Flatpak applications provide `.desktop` files in their exports directory from which display names and icons can be derived.
- **A-003**: The legacy `/var/home/samuel/Projects/cartridges-main` directory is strictly read-only and used solely to understand previous parsing logic.
- **A-004**: Advanced features like browser link pasting or hybrid external search will be considered in a subsequent specification iteration.
- **A-005**: The Preferences dialog layout uses standard Adw.PreferencesPage and Adw.PreferencesGroup widgets to achieve an HIG-compliant presentation.
- **A-006**: A pre-existing database layer or game list storage model exists that can be cleared by the Danger Zone "Remove All" command.
- **A-007**: The user interface implementation is modeled directly after the pre-existing legacy UI structure in the read-only `cartridges-main` reference repository to ensure seamless continuity without introducing any brand-new visual design concepts.

