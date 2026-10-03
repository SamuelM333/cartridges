# Feature Specification: SteamGridDB Cover Picker and Credentials UX

**Feature Branch**: `004-steamgriddb-picker`

**Created**: 2026-10-03

**Status**: Draft

**Input**: User description: "make spec independet. move steamgriddb picker specs from 002 to 004. rename to 004-steamgriddb-picker. review steamgriddb chooser. 1. add a Spinner while the first images are loading 2. Add a Spinner at the bottom of the list while more images are being fetch. Should be horizontally centered in the list 3. Cache images. Clear on exit or expire 4. Hide API key and add an eye icon to show"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mask API Key with Visibility Toggle (Priority: P1)

As a user configuring SteamGridDB integration, I want my API key to be concealed by default in preferences with an eye icon button to reveal it, so that my credentials remain protected from shoulder surfing while still allowing me to verify what I have typed.

**Why this priority**: Protecting credentials from accidental exposure is a fundamental privacy and security requirement across desktop settings.

**Independent Test**: Open Preferences, navigate to the SteamGridDB page, verify that the API key field masks input characters, click the eye icon to verify that text is revealed, and click it again to verify that it is obscured.

**Acceptance Scenarios**:

1. **Given** a user has entered or saved an API key in Preferences, **When** viewing the SteamGridDB settings page, **Then** the key text is masked by default with obscuring glyphs.
2. **Given** the API key field is currently masked, **When** the user clicks the eye icon toggle, **Then** the plain text of the API key becomes visible.
3. **Given** the API key field is currently showing plain text, **When** the user clicks the eye icon toggle again, **Then** the text returns to masked mode.

---

### User Story 2 - Initial Loading Spinner and Dialog Presentation (Priority: P1)

As a player selecting game cover artwork, I want to open an expansive cover picker dialog with an immediate centered loading spinner and properly proportioned candidate thumbnails, so that I can clearly evaluate artwork options without visual clipping or confusion during network retrieval.

**Why this priority**: Sizing the dialog generously and displaying an immediate centered loading indicator prevents blank empty states and ensures high-quality artwork presentation.

**Independent Test**: Trigger "Choose Cover Art" for any game with a populated title; verify the dialog opens with content dimensions of at least 760x520px, displays a centered loading spinner immediately, and renders candidate covers in 2:3 aspect ratio showing full outer borders without clipping or text overlays.

**Acceptance Scenarios**:

1. **Given** a user opens the cover picker for a game, **When** the initial search and first image downloads are in progress, **Then** an active loading spinner is displayed centered in the chooser view within a dialog sized to at least 760x520px content area.
2. **Given** the initial batch of candidate images has finished downloading, **When** the images are added to the display, **Then** the initial centered loading spinner is automatically hidden and candidate covers are rendered in 2:3 aspect ratio showing complete perimeters without clipping or text labels.
3. **Given** the cover search returns no results or encounters an error, **When** fetching finishes, **Then** the initial loading indicator is hidden and an informative empty state message is presented.

---

### User Story 3 - Progressive Batch Loading Spinner (Priority: P2)

As a player browsing extensive cover artwork options, I want to see a centered loading spinner at the bottom of the list while additional images are being fetched, so that I know more candidates are on their way without disrupting images already loaded.

**Why this priority**: Progressive batch loading allows users to browse early results immediately while providing clear visual feedback that background retrieval is still in progress.

**Independent Test**: Open the cover picker for a game with multiple batches of cover candidates; observe a loading spinner positioned at the bottom center of the scrolling list while subsequent images load, which automatically disappears once all candidates have been processed.

**Acceptance Scenarios**:

1. **Given** an initial batch of images is displayed and further candidates are still being fetched, **When** viewing the bottom of the candidate list, **Then** a loading spinner is visible, horizontally centered below the existing candidates.
2. **Given** subsequent images finish downloading and are added to the list, **When** there are no further candidates being fetched, **Then** the bottom spinner is removed.
3. **Given** an error occurs during background fetching of subsequent images, **When** the network attempt concludes, **Then** the bottom spinner is cleanly dismissed without removing previously loaded candidates.

---

### User Story 4 - Cover Image Caching and Expiration Management (Priority: P2)

As a player browsing cover artwork, I want preview images to be cached locally and cleaned up automatically, so that subsequent chooser sessions load quickly without consuming redundant bandwidth or permanently bloating disk storage.

**Why this priority**: Re-downloading external thumbnails consumes user bandwidth and introduces latency; automatic cleanup ensures disk usage remains bounded.

**Independent Test**: Open the cover picker for a title to cache its candidate thumbnails, reopen the picker and observe instant local retrieval, then exit the application or trigger cache expiration and verify temporary preview files are removed.

**Acceptance Scenarios**:

1. **Given** a thumbnail image has been downloaded during a cover picker session, **When** the user views the same candidate again in the same or subsequent session before expiration, **Then** the image is loaded from local cache without initiating an external network download.
2. **Given** temporary cover picker preview files exist in the cache, **When** the application exits or the configured expiration threshold is reached, **Then** the expired or transient preview files are automatically purged.
3. **Given** the cache storage is cleared or missing, **When** opening the cover picker, **Then** the system automatically recreates the necessary cache hierarchy and re-downloads requested preview assets seamlessly.

---

### User Story 5 - Search Triggering and Validation from Game Add/Edit (Priority: P2)

As a user adding or editing a game, I want the SteamGridDB cover button to require a valid game title and visually highlight the field if empty, so that I do not trigger futile searches without search parameters.

**Why this priority**: Clarifying input prerequisites prevents erroneous network requests and guides the user to input a game title before querying external artwork.

**Independent Test**: Open the Add Game or Edit Game dialog with an empty title field; click the SteamGridDB button and verify the Title field is visually styled with an error indicator and the picker does not open; type a valid title and verify the error style clears.

**Acceptance Scenarios**:

1. **Given** a user is adding or editing a game, **When** the Title field is empty, **Then** the Browse files button remains active and clickable, while the SteamGridDB cover button only triggers when the Title value is populated.
2. **Given** the Title field is empty, **When** the user attempts to trigger the SteamGridDB cover button, **Then** the Title field is visually styled with an error indicator and the cover picker dialog is not opened.
3. **Given** the Title field is highlighted with an error indicator, **When** text is entered into the field, **Then** the error styling is cleared immediately.

---

### User Story 6 - Cover Selection and Staging Feedback (Priority: P2)

As a user customizing game artwork, I want to see an active loading spinner over the cover preview in Game Details while my selected cover is being downloaded and processed, so that I have clear visual feedback until staging completes.

**Why this priority**: Downloading high-resolution artwork can take several seconds; explicit feedback over the cover preview assures the user that processing is underway.

**Independent Test**: Select a candidate cover from the cover picker dialog; verify the picker closes, the game details cover preview displays a centered loading spinner, and the spinner dismisses once the new preview image is staged.

**Acceptance Scenarios**:

1. **Given** a cover image is selected from the SteamGridDB cover picker dialog, **When** the image is being fetched and processed for staging, **Then** an active loading spinner is displayed in the game details cover overlay, centered vertically and horizontally over the game cover widget.
2. **Given** the background download and image processing completes or fails, **When** processing concludes, **Then** the loading spinner over the cover preview is automatically dismissed and the staged cover is displayed.

---

### Edge Cases

- What happens when network connectivity is lost while initial images are loading? The initial centered spinner is dismissed and a user-friendly error message or empty state is presented with an option to retry or dismiss.
- What happens when network connectivity is lost while subsequent batches are being fetched? The bottom centered spinner is dismissed gracefully, leaving all already loaded candidate images selectable and intact.
- What happens when a game has zero matching grids on SteamGridDB? The initial spinner is dismissed and an explicit "No covers found" notification is presented.
- What happens when the API key input is completely empty? The field is displayed in its standard empty state and the eye icon toggle remains functional without crashing or displaying invalid placeholders.
- What happens when the local cache directory has restricted permissions or disk is full? The application logs a diagnostic warning and falls back to ephemeral memory loading for previews without crashing the UI.
- What happens when the user clicks the SteamGridDB button while Title contains only whitespace? It is treated as empty, triggering the Title error styling and preventing picker launch.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display an expanded SteamGridDB cover picker dialog with content dimensions of at least 760x520 pixels.
- **FR-002**: System MUST render each candidate cover thumbnail within the picker in a 2:3 aspect ratio matching the game details cover view, ensuring the entire artwork and its complete outer borders are fully visible without cropping, clipping, or caption overlays.
- **FR-003**: System MUST display an active loading spinner centered within the cover picker dialog immediately upon opening, while the initial batch of candidate images is being queried and fetched.
- **FR-004**: System MUST dismiss the initial centered loading spinner as soon as the first batch of candidate covers is rendered, or when the query resolves with an empty state or error.
- **FR-005**: System MUST display a horizontally centered loading spinner at the bottom of the candidate list whenever additional candidate images are actively being fetched or processed.
- **FR-006**: System MUST dismiss the bottom centered loading spinner when all additional image fetching operations have concluded or encountered an error.
- **FR-007**: System MUST mask the SteamGridDB API key input field by default in the application preferences.
- **FR-008**: System MUST provide an interactive reveal/hide toggle action (eye icon) alongside the API key input to switch between masked characters and plain text.
- **FR-009**: System MUST store downloaded cover picker preview images in a dedicated local cache directory conforming to platform cache conventions.
- **FR-010**: System MUST retrieve preview images from the local cache rather than the network when a valid cached copy exists for a requested thumbnail URL.
- **FR-011**: System MUST automatically purge transient preview cache files upon application exit or when entries exceed their designated expiration age.
- **FR-012**: System MUST only allow opening the SteamGridDB cover picker when a non-empty game Title is provided; if triggered with an empty Title, the Title input field MUST be styled with a visual error indicator and the picker MUST NOT open.
- **FR-013**: When a candidate cover is selected from the picker, the cover overlay in Game Details MUST display a centered loading spinner over the cover preview widget throughout background downloading and staging.
- **FR-014**: All network queries, thumbnail caching, and image decoding routines MUST execute asynchronously without blocking the user interface main loop.

### Key Entities

- **Cover Candidate**: Represents an artwork option retrieved from SteamGridDB, including thumbnail preview data, full resolution artwork URL, and visual properties.
- **Preview Cache**: Local persistent or transient cache store indexed by candidate identifier or thumbnail URL, containing image bytes and timestamp metadata for expiration management.
- **API Key Credential**: Authentication secret utilized to access the SteamGridDB service, managed securely in settings with masked display and interactive reveal capabilities.
- **Picker Dialog State**: State machine managing the presentation of the picker dialog across initial loading, results with progressive pagination, and empty/error conditions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of candidate covers shown in the cover picker dialog match the 2:3 aspect ratio, showing complete perimeters without border clipping or overlay text, inside an expanded dialog of at least 760x520px content size.
- **SC-002**: An active loading spinner is visible within 100 milliseconds of opening the cover chooser dialog whenever candidate images are not yet ready.
- **SC-003**: 100% of progressive or subsequent cover fetch operations display a horizontally centered spinner at the bottom of the list until all downloads for that batch complete.
- **SC-004**: Reopening the cover picker for previously fetched items loads preview thumbnails from local cache in under 300 milliseconds under normal system conditions.
- **SC-005**: 100% of temporary preview cache files are cleaned up either on application exit or when exceeding the defined expiration window, preventing unbounded disk growth.
- **SC-006**: The SteamGridDB API key is 100% masked on initial display in preferences, and toggling the eye icon updates the visibility mode instantaneously without modifying the underlying stored key.
- **SC-007**: Triggering SteamGridDB cover search with an empty Title highlights the field with an error style 100% of the time and prevents dialog launch, reverting to normal styling once text is entered.
- **SC-008**: 100% of SteamGridDB cover downloads in Game Details display an active loading spinner centered horizontally and vertically over the cover preview from the moment a candidate is chosen until the newly processed cover is rendered or cancelled.

## Assumptions

- The SteamGridDB API key configuration is housed within the application preferences dialog under the SteamGridDB section.
- Preview images are stored in the user cache directory under the application's XDG cache path.
- Cache entries have a default expiration window of 7 days if not cleared on application exit.
- The cover chooser presents candidates in a scrollable grid format, accommodating an initial batch followed by progressive loading of subsequent candidates.
- Staging cover artwork in Game Details holds modifications until the user explicitly commits them with "Apply".
